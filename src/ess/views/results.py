import formencode

from collections import Counter
from csv import DictWriter
from datetime import datetime, timedelta
from io import StringIO
from pyramid.httpexceptions import HTTPNotFound
from pyramid.response import Response
from pyramid.view import view_config
from pywebtools.formencode import CSRFSchema, State
from pywebtools.pyramid.auth.views import current_user, require_permission
from pywebtools.sqlalchemy import DBSession
from sqlalchemy import and_, func

from ess.models import Experiment, Participant, Question, Answer, Page


def init(config):
    config.add_route('experiment.results', '/experiments/{eid}/results')
    config.add_route('experiment.results.export', '/experiments/{eid}/results/export')


@view_config(route_name='experiment.results', renderer='ess:templates/results/overview.kajiki')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='view')
def overview(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    if experiment:
        time_boundary = datetime.now() - timedelta(minutes=20)
        overall = {'total': dbsession.query(func.count(Participant.id.unique)).filter(Participant.experiment_id == experiment.id).first()[0],
                   'completed': dbsession.query(func.count(Participant.id.unique)).filter(and_(Participant.experiment_id == experiment.id,
                                                                                               Participant.completed == True)).first()[0],
                   'in_progress': dbsession.query(func.count(Participant.id.unique)).filter(and_(Participant.experiment_id == experiment.id,
                                                                                                 Participant.completed == False,
                                                                                                 Participant.updated >= time_boundary)).first()[0],
                   'abandoned': dbsession.query(func.count(Participant.id.unique)).filter(and_(Participant.experiment_id == experiment.id,
                                                                                               Participant.completed == False,
                                                                                               Participant.updated < time_boundary)).first()[0]}
        
        in_progress = {}
        abandoned = {}
        for participant in dbsession.query(Participant).filter(and_(Participant.experiment_id == experiment.id,
                                                                    Participant.completed == False)):
            if participant.updated >= time_boundary:
                if participant['current'] in in_progress:
                    in_progress[participant['current']] = in_progress[participant['current']] + 1
                else:
                    in_progress[participant['current']] = 1
            else:
                if participant['current'] in abandoned:
                    abandoned[participant['current']] = abandoned[participant['current']] + 1
                else:
                    abandoned[participant['current']] = 1
        summary = {}
        for answer in dbsession.query(Answer).join(Participant).join(Question).join(Page).filter(and_(Participant.experiment_id == experiment.id,
                                                                                                      Participant.completed == True)):
            if answer.question.page.id not in summary:
                summary[answer.question.page.id] = {'questions': {}}
            if answer.question['frontend', 'display_as'] == 'simple_input':
                if answer.question.id not in summary[answer.question.page.id]['questions']:
                    summary[answer.question.page.id]['questions'][answer.question.id] = Counter()
                if answer['response']:
                    summary[answer.question.page.id]['questions'][answer.question.id].update([answer['response']])
            elif answer.question['frontend', 'display_as'] == 'select_simple_choice':
                if answer.question.id not in summary[answer.question.page.id]['questions']:
                    summary[answer.question.page.id]['questions'][answer.question.id] = Counter()
                if isinstance(answer['response'], list):
                    summary[answer.question.page.id]['questions'][answer.question.id].update(answer['response'])
                else:
                    summary[answer.question.page.id]['questions'][answer.question.id].update([answer['response']])
            elif answer.question['frontend', 'display_as'] == 'select_grid_choice':
                if answer.question.id not in summary[answer.question.page.id]['questions']:
                    summary[answer.question.page.id]['questions'][answer.question.id] = {}
                for key, value in answer['response'].items():
                    if key not in summary[answer.question.page.id]['questions'][answer.question.id]:
                        summary[answer.question.page.id]['questions'][answer.question.id][key] = Counter()
                    if isinstance(value, list):
                        summary[answer.question.page.id]['questions'][answer.question.id][key].update(value)
                    else:
                        summary[answer.question.page.id]['questions'][answer.question.id][key].update([value])
            elif answer.question['frontend', 'display_as'] == 'ranking':
                if answer.question.id not in summary[answer.question.page.id]['questions']:
                    summary[answer.question.page.id]['questions'][answer.question.id] = Counter()
                summary[answer.question.page.id]['questions'][answer.question.id].update([' - '.join(answer['response'])])
            if answer.question.page.dataset_id is not None:
                if 'dataset' not in summary[answer.question.page.id]:
                    summary[answer.question.page.id]['dataset'] = Counter()
                summary[answer.question.page.id]['dataset'].update([answer.data_item_id])
        return {'experiment': experiment,
                'overall': overall,
                'in_progress': in_progress,
                'abandoned': abandoned,
                'summary': summary,
                'crumbs': [{'title': 'Experiments',
                            'url': request.route_url('dashboard')},
                           {'title': experiment.title,
                            'url': request.route_url('experiment.view', eid=experiment.id)},
                           {'title': 'Results',
                            'url': request.route_url('experiment.results', eid=experiment.id)}]}
    else:
        raise HTTPNotFound()


class ExportSchema(CSRFSchema):

    na_value = formencode.validators.UnicodeString(not_empty=True)
    include_incomplete = formencode.validators.StringBool(if_missing=False, if_empty=False)
    include_useragent = formencode.validators.StringBool(if_missing=False, if_empty=False)


@view_config(route_name='experiment.results.export', renderer='ess:templates/results/export.kajiki')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='view')
def export_settings(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    if experiment:
        if request.method == 'POST':
            try:
                schema = ExportSchema()
                questions = [str(q.id) for p in experiment.pages for q in p.questions if q['frontend', 'display_as'] != 'text']
                schema.add_field('question', formencode.ForEach(formencode.validators.OneOf(questions, not_empty=True)))
                for data_set in experiment.data_sets:
                    schema.add_field('data_set_identifier_%s' % data_set.id, formencode.validators.OneOf(['_id'] + [str(c) for c in data_set['columns']]))
                params = schema.to_python(request.params, State(request=request))
                def data_item_column_mapper(data_item):
                    if params['data_set_identifier_%s' % data_item.dataset_id] == '_id':
                        return data_item.id
                    else:
                        return data_item['values'][params['data_set_identifier_%s' % data_item.dataset_id]]
                columns = set(['_participant'])
                if params['include_incomplete']:
                    query = dbsession.query(Participant).filter(and_(Participant.experiment_id == experiment.id))
                    columns.add('_completed')
                else:
                    query = dbsession.query(Participant).filter(and_(Participant.experiment_id == experiment.id,
                                                                            Participant.completed == True))
                if params['include_useragent']:
                    columns.add('_user_agent.screen_size')
                    columns.add('_user_agent.string')
                for participant in query:
                    if params['include_useragent']:
                        if 'user_agent' in participant:
                            if 'input_types' in participant['user_agent']:
                                columns.update(['_user_agent.input_type.%s' % input_type for input_type in participant['user_agent']['input_types']])
                    for answer in participant.answers:
                        if str(answer.question.id) not in params['question']:
                            continue
                        column = '%s.%s' % (answer.question.page.name, answer.question['name'])
                        new_columns = []
                        if answer.question['frontend', 'display_as'] == 'select_grid_choice':
                            for key, value in answer['response'].items():
                                sub_column = '%s.%s' % (column, key)
                                if answer.question['frontend', 'allow_multiple']:
                                    if isinstance(value, list):
                                        sub_column = ['%s.%s' % (sub_column, a) for a in value]
                                    else:
                                        sub_column = ['%s.%s' % (sub_column, value)]
                                else:
                                    sub_column = [sub_column]
                                new_columns.extend(sub_column)
                        elif answer.question['frontend', 'display_as'] == 'ranking':
                            new_columns.extend(['%s.%s' % (column, a['value']) for a in answer.question['frontend', 'answers']])
                        else:
                            if answer.question['frontend', 'allow_multiple']:
                                if isinstance(answer['response'], list):
                                    new_columns = ['%s.%s' % (column, a) for a in answer['response']]
                                else:
                                    new_columns = ['%s.%s' % (column, answer['response'])]
                            else:
                                new_columns = [column]
                        if answer.question.page.dataset_id is not None:
                            new_columns = ['%s.%s' % (c, data_item_column_mapper(di)) for c in new_columns for di in answer.question.page.data_set.items]
                        columns.update(new_columns)
                columns = list(columns)
                columns.sort(key=lambda k: k.split('.'))
                io = StringIO()
                writer = DictWriter(io, fieldnames=columns, restval=params['na_value'], extrasaction='ignore')
                writer.writeheader()
                for participant in query.order_by(Participant.id):
                    responses = {'_participant': participant.id}
                    if params['include_incomplete']:
                        responses['_completed'] = participant.completed
                    if params['include_useragent']:
                        if 'user_agent' in participant:
                            if 'input_types' in participant['user_agent']:
                                for column in columns:
                                    if column.startswith('_user_agent.input_type.'):
                                        responses[column] = 0
                                for input_type in participant['user_agent']['input_types']:
                                    responses['_user_agent.input_type.%s' % input_type] = 1
                            if 'screen_size' in participant['user_agent']:
                                responses['_user_agent.screen_size'] = participant['user_agent']['screen_size']
                            if 'user_agent' in participant['user_agent']:
                                responses['_user_agent.string'] = participant['user_agent']['user_agent']
                    for answer in participant.answers:
                        column = '%s.%s' % (answer.question.page.name, answer.question['name'])
                        if answer.question['frontend', 'display_as'] == 'select_grid_choice':
                            for key, value in answer['response'].items():
                                sub_column = '%s.%s' % (column, key)
                                if answer.question['frontend', 'allow_multiple']:
                                    for c in columns:
                                        if c.startswith(sub_column):
                                            responses[c] = 0
                                    if isinstance(value, list):
                                        for sub_answer in value:
                                            if answer.data_item_id is None:
                                                responses['%s.%s' % (sub_column, sub_answer)] = 1
                                            else:
                                                responses['%s.%s.%s' % (sub_column, sub_answer, data_item_column_mapper(answer.data_item))] = 1
                                    else:
                                        if answer.data_item_id is None:
                                            responses['%s.%s' % (sub_column, value)] = 1
                                        else:
                                            responses['%s.%s.%s' % (sub_column, value, data_item_column_mapper(answer.data_item))] = 1
                                else:
                                    if answer.data_item_id is None:
                                        responses[sub_column] = value
                                    else:
                                        responses['%s.%s' % (sub_column, data_item_column_mapper(answer.data_item))] = value
                        elif answer.question['frontend', 'display_as'] == 'ranking':
                            for idx, sub_answer in enumerate(answer['response']):
                                if answer.data_item_id is None:
                                    responses['%s.%s' % (column, sub_answer)] = idx
                                else:
                                    responses['%s.%s.%s' % (column, sub_answer, data_item_column_mapper(answer.data_item))] = idx
                        else:
                            if answer.question['frontend', 'allow_multiple']:
                                for c in columns:
                                    if c.startswith(column):
                                        responses[c] = 0
                                if isinstance(answer['response'], list):
                                    for sub_answer in answer['response']:
                                        if answer.data_item_id is None:
                                            responses['%s.%s' % (column, sub_answer)] = 1
                                        else:
                                            responses['%s.%s.%s' % (column, sub_answer, data_item_column_mapper(answer.data_item))] = 1
                                else:
                                    if answer.data_item_id is None:
                                        responses['%s.%s' % (column, answer['response'])] = 1
                                    else:
                                        responses['%s.%s.%s' % (column, answer['response'], data_item_column_mapper(answer.data_item))] = 1
                            else:
                                if answer.data_item_id is None:
                                    responses[column] = answer['response']
                                else:
                                    responses['%s.%s' % (column, data_item_column_mapper(answer.data_item))] = answer['response']
                    writer.writerow(responses)
                return Response(body=io.getvalue().encode('utf8'),
                                headers=[('Content-Type', 'text/csv'),
                                         ('Content-Disposition', 'attachment; filename="%s.csv"' % experiment.title)])
            except formencode.Invalid as e:
                return {'experiment': experiment,
                        'values': request.params,
                        'errors': e.error_dict,
                        'crumbs': [{'title': 'Experiments',
                                    'url': request.route_url('dashboard')},
                                   {'title': experiment.title,
                                    'url': request.route_url('experiment.view', eid=experiment.id)},
                                   {'title': 'Results',
                                    'url': request.route_url('experiment.results', eid=experiment.id)},
                                   {'title': 'Export',
                                    'url': request.route_url('experiment.results.export', eid=experiment.id)}]}                
        return {'experiment': experiment,
                'crumbs': [{'title': 'Experiments',
                            'url': request.route_url('dashboard')},
                           {'title': experiment.title,
                            'url': request.route_url('experiment.view', eid=experiment.id)},
                           {'title': 'Results',
                            'url': request.route_url('experiment.results', eid=experiment.id)},
                           {'title': 'Export',
                            'url': request.route_url('experiment.results.export', eid=experiment.id)}]}
    else:
        raise HTTPNotFound()
