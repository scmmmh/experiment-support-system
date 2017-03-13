import formencode
import transaction

from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.renderers import render_to_response
from pyramid.view import view_config
from pywebtools.formencode import CSRFSchema, State
from pywebtools.pyramid.auth.views import current_user, require_permission
from pywebtools.pyramid.decorators import require_method
from pywebtools.sqlalchemy import DBSession
from sqlalchemy import and_

from ess.importexport import PageIOSchema, import_jsonapi, export_jsonapi
from ess.models import Experiment, Page, QuestionTypeGroup, Question, QuestionType, Transition, DataSet
from ess.validators import PageNameUniqueValidator, QuestionEditSchema, PageExistsValidator, QuestionExistsValidator, DataSetExistsValidator


def init(config):
    config.add_route('experiment.page', '/experiments/{eid}/pages')
    config.add_route('experiment.page.create', '/experiments/{eid}/pages/create')
    config.add_route('experiment.page.import', '/experiments/{eid}/pages/import')
    config.add_route('experiment.page.edit', '/experiments/{eid}/pages/{pid}')
    config.add_route('experiment.page.edit.add_question', '/experiments/{eid}/pages/{pid}/add_question/{qtid}')
    config.add_route('experiment.page.edit.question', '/experiments/{eid}/pages/{pid}/questions/{qid}/edit')
    config.add_route('experiment.page.edit.reorder', '/experiments/{eid}/pages/{pid}/reorder')
    config.add_route('experiment.page.delete.question', '/experiments/{eid}/pages/{pid}/questions/{qid}/delete')
    config.add_route('experiment.page.transition', '/experiments/{eid}/pages/{pid}/transitions')
    config.add_route('experiment.page.transition.add', '/experiments/{eid}/pages/{pid}/transitions/add')
    config.add_route('experiment.page.transition.reorder', '/experiments/{eid}/pages/{pid}/transitions/reorder')
    config.add_route('experiment.page.transition.edit', '/experiments/{eid}/pages/{pid}/transitions/{tid}/edit')
    config.add_route('experiment.page.transition.delete', '/experiments/{eid}/pages/{pid}/transitions/{tid}/delete')
    config.add_route('experiment.page.data', '/experiments/{eid}/pages/{pid}/data')
    config.add_route('experiment.page.settings', '/experiments/{eid}/pages/{pid}/settings')
    config.add_route('experiment.page.export', '/experiments/{eid}/pages/{pid}/export')


@view_config(route_name='experiment.page', renderer='ess:templates/page/list.kajiki')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='view')
def page_list(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    if experiment:
        return {'experiment': experiment,
                'crumbs': [{'title': 'Experiments',
                            'url': request.route_url('dashboard')},
                           {'title': experiment.title,
                            'url': request.route_url('experiment.view', eid=experiment.id)},
                           {'title': 'Pages',
                            'url': request.route_url('experiment.page', eid=experiment.id)}]}
    else:
        raise HTTPNotFound()


class CreatePageSchema(CSRFSchema):

    name = formencode.Pipe(formencode.validators.UnicodeString(not_empty=True,
                                                               messages={'empty': 'Please provide a unique name'}),
                           PageNameUniqueValidator())
    title = formencode.validators.UnicodeString()


@view_config(route_name='experiment.page.create', renderer='ess:templates/page/create.kajiki')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
def create(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    if experiment:
        if request.method == 'POST':
            try:
                params = CreatePageSchema().to_python(request.params, State(request=request,
                                                                            dbsession=dbsession,
                                                                            experiment=experiment))
                with transaction.manager:
                    page = Page(experiment=experiment,
                                name=params['name'],
                                title=params['title'],
                                styles='',
                                scripts='')
                    dbsession.add(page)
                dbsession.add(experiment)
                dbsession.add(page)
                raise HTTPFound(request.route_url('experiment.page.edit', eid=experiment.id, pid=page.id))
            except formencode.Invalid as e:
                return {'experiment': experiment,
                        'crumbs': [{'title': 'Experiments',
                                    'url': request.route_url('dashboard')},
                                   {'title': experiment.title,
                                    'url': request.route_url('experiment.view', eid=experiment.id)},
                                   {'title': 'Pages',
                                    'url': request.route_url('experiment.page', eid=experiment.id)},
                                   {'title': 'Add a Page',
                                    'url': request.route_url('experiment.page.create', eid=experiment.id)}],
                        'errors': e.error_dict,
                        'values': request.params}
        return {'experiment': experiment,
                'crumbs': [{'title': 'Experiments',
                            'url': request.route_url('dashboard')},
                           {'title': experiment.title,
                            'url': request.route_url('experiment.view', eid=experiment.id)},
                           {'title': 'Pages',
                            'url': request.route_url('experiment.page', eid=experiment.id)},
                           {'title': 'Add a Page',
                            'url': request.route_url('experiment.page.create', eid=experiment.id)}]}
    else:
        raise HTTPNotFound()


class ImportPageSchema(CSRFSchema):

    source = formencode.validators.FieldStorageUploadConverter(not_empty=True)


@view_config(route_name='experiment.page.import', renderer='ess:templates/page/import.kajiki')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
def import_page(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    if experiment:
        if request.method == 'POST':
            try:
                params = ImportPageSchema().to_python(request.params, State(request=request,
                                                                            dbsession=dbsession))
                with transaction.manager:
                    dbsession.add(experiment)
                    page = import_jsonapi(params['source'].file.read().decode('utf-8'),
                                          dbsession,
                                          State(experiment_id=experiment.id))
                    if not isinstance(page, Page):
                        raise formencode.Invalid('The file does not contain a page.')
                    page.experiment = experiment
                    dbsession.add(page)
                dbsession.add(experiment)
                dbsession.add(page)
                raise HTTPFound(request.route_url('experiment.page.edit', eid=experiment.id, pid=page.id))
            except formencode.Invalid as e:
                return {'experiment': experiment,
                        'crumbs': [{'title': 'Experiments',
                                    'url': request.route_url('dashboard')},
                                   {'title': experiment.title,
                                    'url': request.route_url('experiment.view', eid=experiment.id)},
                                   {'title': 'Pages',
                                    'url': request.route_url('experiment.page', eid=experiment.id)},
                                   {'title': 'Add a Page',
                                    'url': request.route_url('experiment.page.create', eid=experiment.id)}],
                        'errors': {'source': str(e)},
                        'values': request.params}
        return {'experiment': experiment,
                'crumbs': [{'title': 'Experiments',
                            'url': request.route_url('dashboard')},
                           {'title': experiment.title,
                            'url': request.route_url('experiment.view', eid=experiment.id)},
                           {'title': 'Pages',
                            'url': request.route_url('experiment.page', eid=experiment.id)},
                           {'title': 'Add a Page',
                            'url': request.route_url('experiment.page.create', eid=experiment.id)}]}
    else:
        raise HTTPNotFound()


@view_config(route_name='experiment.page.edit', renderer='ess:templates/page/edit.kajiki')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='view')
def edit(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    if experiment:
        page = dbsession.query(Page).filter(and_(Page.id == request.matchdict['pid'],
                                                 Page.experiment == experiment)).first()
    else:
        page = None
    if experiment and page:
        qtgroups = dbsession.query(QuestionTypeGroup).filter(QuestionTypeGroup.parent_id == None).\
            order_by(QuestionTypeGroup.order)
        return {'experiment': experiment,
                'page': page,
                'qtgroups': qtgroups,
                'crumbs': [{'title': 'Experiments',
                            'url': request.route_url('dashboard')},
                           {'title': experiment.title,
                            'url': request.route_url('experiment.view', eid=experiment.id)},
                           {'title': 'Pages',
                            'url': request.route_url('experiment.page', eid=experiment.id)},
                           {'title': '%s (%s)' % (page.title, page.name)
                            if page.title else 'No title (%s)' % page.name,
                            'url': request.route_url('experiment.page.edit', eid=experiment.id, pid=page.id)}]}
    else:
        raise HTTPNotFound()


@view_config(route_name='experiment.page.edit.question', renderer='json')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
@require_method('POST')
def edit_question(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    if experiment:
        page = dbsession.query(Page).filter(and_(Page.id == request.matchdict['pid'],
                                                 Page.experiment == experiment)).first()
    else:
        page = None
    if page:
        question = dbsession.query(Question).filter(and_(Question.id == request.matchdict['qid'],
                                                         Question.page == page)).first()
    else:
        question = None
    if experiment and page and question:
        try:
            params = QuestionEditSchema(question['backend', 'fields']).to_python(request.params, State(request=request,
                                                                                  dbsession=dbsession))
            with transaction.manager:
                dbsession.add(question)
                # Update question parameters
                for key, value in params.items():
                    if isinstance(value, list):
                        new_value = []
                        for sub_value in value:
                            if isinstance(sub_value, dict):
                                if len([v for v in sub_value.values() if v is None]) == 0:
                                    new_value.append(sub_value)
                            else:
                                if sub_value is not None:
                                    new_value.append(sub_value)
                        value = new_value
                    if key != 'csrf_token':
                        question[key] = value
                # Update all question numbering
                dbsession.add(page)
                visible_idx = 1
                for q in page.questions:
                    if q['frontend', 'visible'] and q['frontend', 'title']:
                        q['frontend', 'question_number'] = visible_idx
                        visible_idx = visible_idx + 1
            dbsession.add(experiment)
            dbsession.add(page)
            dbsession.add(question)
            data = render_to_response('ess:templates/page/edit_question.kajiki',
                                                   {'experiment': experiment,
                                                    'page': page,
                                                    'question': question},
                                                    request=request)
            return {'status': 'ok',
                    'fragment': data.body.decode('utf-8')}
        except formencode.Invalid as e:
            return {'status': 'error',
                    'errors': e.unpack_errors()}
    else:
        raise HTTPNotFound()


class ReorderSchema(CSRFSchema):

    item = formencode.foreach.ForEach(formencode.validators.Int, convert_to_list=True)


@view_config(route_name='experiment.page.edit.reorder', renderer='json')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
@require_method('POST')
def reorder_page(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    if experiment:
        page = dbsession.query(Page).filter(and_(Page.id == request.matchdict['pid'],
                                                 Page.experiment == experiment)).first()
    else:
        page = None
    if experiment and page:
        try:
            params = ReorderSchema().to_python(request.params, State(request=request))
            with transaction.manager:
                visible_idx = 1
                for idx, qid in enumerate(params['item']):
                    question = dbsession.query(Question).filter(and_(Question.id == qid,
                                                                     Question.page == page)).first()
                    if question is not None:
                        dbsession.add(question.q_type)
                        question.order = idx
                        if question['frontend', 'visible'] and question['frontend', 'title']:
                            question['frontend', 'question_number'] = visible_idx
                            visible_idx = visible_idx + 1
            return {'status': 'ok'}
        except formencode.Invalid:
            return {'status': 'error'}
    else:
        raise HTTPNotFound()


class AddQuestionSchema(CSRFSchema):

    order = formencode.validators.Int(if_missing=None, if_empty=None)


@view_config(route_name='experiment.page.edit.add_question', renderer='json')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
@require_method('POST')
def add_question(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    if experiment:
        page = dbsession.query(Page).filter(and_(Page.id == request.matchdict['pid'],
                                                 Page.experiment == experiment)).first()
    else:
        page = None
    qtype = dbsession.query(QuestionType).filter(QuestionType.id == request.matchdict['qtid']).first()
    if experiment and page and qtype:
        try:
            params = AddQuestionSchema().to_python(request.params, State(request=request))
            with transaction.manager:
                dbsession.add(page)
                if params['order'] is None:
                    params['order'] = len(page.questions)
                question = Question(q_type=qtype,
                                    page=page,
                                    order=params['order'])
                if question['frontend', 'visible']:
                    visible_idx = [q['frontend', 'question_number'] for q in page.questions if q['frontend', 'visible'] and q['frontend', 'title'] and q['frontend', 'question_number']]
                    if visible_idx:
                        visible_idx = max(visible_idx) + 1
                    else:
                        visible_idx = 1
                    question['frontend', 'question_number'] = visible_idx
                dbsession.add(question)
            dbsession.add(experiment)
            dbsession.add(page)
            dbsession.add(question)
            raise HTTPFound(request.route_url('experiment.page.edit', eid=experiment.id, pid=page.id, _anchor='question-%i' % question.id))
        except formencode.Invalid:
            raise HTTPFound(request.route_url('experiment.page.edit', eid=experiment.id, pid=page.id))
    else:
        raise HTTPNotFound()


@view_config(route_name='experiment.page.delete.question', renderer='json')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
@require_method('POST')
def delete_question(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    if experiment:
        page = dbsession.query(Page).filter(and_(Page.id == request.matchdict['pid'],
                                                 Page.experiment == experiment)).first()
    else:
        page = None
    if page:
        question = dbsession.query(Question).filter(and_(Question.id == request.matchdict['qid'],
                                                         Question.page == page)).first()
    else:
        question = None
    if experiment and page and question:
        try:
            with transaction.manager:
                dbsession.delete(question)
            dbsession.add(experiment)
            dbsession.add(page)
            raise HTTPFound(request.route_url('experiment.page.edit', eid=experiment.id, pid=page.id))
        except formencode.Invalid:
            raise HTTPFound(request.route_url('experiment.page.edit', eid=experiment.id, pid=page.id))
    else:
        raise HTTPNotFound()


@view_config(route_name='experiment.page.transition', renderer='ess:templates/page/transition.kajiki')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='view')
def transitions(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    if experiment:
        page = dbsession.query(Page).filter(and_(Page.id == request.matchdict['pid'],
                                                 Page.experiment == experiment)).first()
    else:
        page = None
    if experiment and page:
        pages_questions = {}
        for tmp_page in experiment.pages:
            pages_questions[tmp_page.id] = {'page': tmp_page,
                                            'questions': dict([(q.id, q) for q in tmp_page.questions])}
        return {'experiment': experiment,
                'page': page,
                'pages_questions': pages_questions,
                'crumbs': [{'title': 'Experiments',
                            'url': request.route_url('dashboard')},
                           {'title': experiment.title,
                            'url': request.route_url('experiment.view', eid=experiment.id)},
                           {'title': 'Pages',
                            'url': request.route_url('experiment.page', eid=experiment.id)},
                           {'title': '%s (%s)' % (page.title, page.name)
                            if page.title else 'No title (%s)' % page.name,
                            'url': request.route_url('experiment.page.edit', eid=experiment.id, pid=page.id)}]}
    else:
        raise HTTPNotFound()


class TransitionEditSchema(CSRFSchema):

    target = PageExistsValidator()
    condition = formencode.validators.OneOf(['', 'answer', 'dataset', 'latinsquare'])


@view_config(route_name='experiment.page.transition.edit', renderer='json')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
@require_method('POST')
def edit_transition(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    if experiment:
        page = dbsession.query(Page).filter(and_(Page.id == request.matchdict['pid'],
                                                 Page.experiment == experiment)).first()
    else:
        page = None
    if page:
        transition = dbsession.query(Transition).filter(and_(Transition.id == request.matchdict['tid'],
                                                             Transition.source == page)).first()
    else:
        transition = None
    if experiment and page and transition:
        try:
            schema = TransitionEditSchema()
            if 'condition' in request.params:
                if request.params['condition'] == 'answer':
                    schema.add_field('condition_answer_page', PageExistsValidator(not_empty=True))
                    schema.add_field('condition_answer_question', QuestionExistsValidator(request.params['condition_answer_page'] if 'condition_answer_page' in request.params else '', not_empty=True))
                    schema.add_field('condition_answer_value', formencode.validators.UnicodeString())
            params = schema.to_python(request.params, State(request=request,
                                                            dbsession=dbsession,
                                                            experiment=experiment,
                                                            page=page))
            with transaction.manager:
                transition.target_id = params['target']
                if params['condition'] == '':
                    if 'condition' in transition:
                        del transition['condition']
                else:
                    if params['condition'] == 'answer':
                        transition['condition'] = {'type': 'answer',
                                                   'page': params['condition_answer_page'],
                                                   'question': params['condition_answer_question'],
                                                   'value': params['condition_answer_value']}
                    elif params['condition'] == 'dataset':
                        transition['condition'] = {'type': 'dataset'}
                    elif params['condition'] == 'latinsquare':
                        transition['condition'] = {'type': 'latinsquare'}
                dbsession.add(transition)
            dbsession.add(experiment)
            dbsession.add(page)
            dbsession.add(transition)
            pages_questions = {}
            for tmp_page in experiment.pages:
                pages_questions[tmp_page.id] = {'page': tmp_page,
                                                'questions': dict([(q.id, q) for q in tmp_page.questions])}
            data = render_to_response('ess:templates/page/edit_transition.kajiki',
                                      {'experiment': experiment,
                                       'page': page,
                                       'transition': transition,
                                       'pages_questions': pages_questions},
                                       request=request)
            return {'status': 'ok',
                    'fragment': data.body.decode('utf-8')}
        except formencode.Invalid as e:
            return {'status': 'error',
                    'errors': e.unpack_errors()}
    else:
        raise HTTPNotFound()


@view_config(route_name='experiment.page.transition.reorder', renderer='json')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
@require_method('POST')
def reorder_transition(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    if experiment:
        page = dbsession.query(Page).filter(and_(Page.id == request.matchdict['pid'],
                                                 Page.experiment == experiment)).first()
    else:
        page = None
    if experiment and page:
        try:
            params = ReorderSchema().to_python(request.params, State(request=request))
            with transaction.manager:
                for idx, tid in enumerate(params['item']):
                    transition = dbsession.query(Transition).filter(and_(Transition.id == tid,
                                                                         Transition.source == page)).first()
                    if transition is not None:
                        transition.order = idx
            return {'status': 'ok'}
        except formencode.Invalid:
            return {'status': 'error'}
    else:
        raise HTTPNotFound()


@view_config(route_name='experiment.page.transition.delete', renderer='json')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
@require_method('POST')
def delete_transition(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    if experiment:
        page = dbsession.query(Page).filter(and_(Page.id == request.matchdict['pid'],
                                                 Page.experiment == experiment)).first()
    else:
        page = None
    if page:
        transition = dbsession.query(Transition).filter(and_(Transition.id == request.matchdict['tid'],
                                                             Transition.source == page)).first()
    else:
        transition = None
    if experiment and page and transition:
        try:
            with transaction.manager:
                dbsession.delete(transition)
            dbsession.add(experiment)
            dbsession.add(page)
            raise HTTPFound(request.route_url('experiment.page.transition', eid=experiment.id, pid=page.id))
        except formencode.Invalid:
            raise HTTPFound(request.route_url('experiment.page.transition', eid=experiment.id, pid=page.id))
    else:
        raise HTTPNotFound()


@view_config(route_name='experiment.page.transition.add', renderer='json')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
@require_method('POST')
def add_transition(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    if experiment:
        page = dbsession.query(Page).filter(and_(Page.id == request.matchdict['pid'],
                                                 Page.experiment == experiment)).first()
    else:
        page = None
    if experiment and page:
        try:
            with transaction.manager:
                dbsession.add(page)
                if page.next:
                    order = max([t.order for t in page.next]) + 1
                else:
                    order = 1
                transition = Transition(source=page, order=order)
                dbsession.add(transition)
            dbsession.add(experiment)
            dbsession.add(page)
            dbsession.add(transition)
            raise HTTPFound(request.route_url('experiment.page.transition', eid=experiment.id, pid=page.id, _anchor='transition-%i' % transition.id))
        except formencode.Invalid:
            raise HTTPFound(request.route_url('experiment.page.transition', eid=experiment.id, pid=page.id))
    else:
        raise HTTPNotFound()


class DataAttachmentSchema(CSRFSchema):

    data_set = DataSetExistsValidator(if_empty=None, if_missing=None)


@view_config(route_name='experiment.page.data', renderer='ess:templates/page/data.kajiki')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
def data(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    page = dbsession.query(Page).filter(and_(Page.id == request.matchdict['pid'],
                                             Page.experiment_id == request.matchdict['eid'])).first()
    if experiment and page:
        data_sets = dbsession.query(DataSet).filter(DataSet.experiment_id == experiment.id)
        if request.method == 'POST':
            try:
                schema = DataAttachmentSchema()
                mode = ''
                if 'data_set' in request.params and request.params['data_set'] in [str(ds.id) for ds in data_sets if ds.type == 'dataset']:
                    schema.add_field('data_items', formencode.validators.Int(not_empty=True))
                    mode = 'dataset'
                params = schema.to_python(request.params, State(request=request,
                                                                dbsession=dbsession,
                                                                experiment=experiment))
                with transaction.manager:
                    dbsession.add(page)
                    page.dataset_id = params['data_set']
                    if mode == 'dataset':
                        page['data'] = {'type': 'dataset',
                                        'item_count': params['data_items']}
                dbsession.add(experiment)
                dbsession.add(page)
                raise HTTPFound(request.route_url('experiment.page.data', eid=experiment.id, pid=page.id))
            except formencode.Invalid as e:
                return {'experiment': experiment,
                        'page': page,
                        'data_sets': data_sets,
                        'crumbs': [{'title': 'Experiments',
                                    'url': request.route_url('dashboard')},
                                   {'title': experiment.title,
                                    'url': request.route_url('experiment.view', eid=experiment.id)},
                                   {'title': 'Pages',
                                    'url': request.route_url('experiment.page', eid=experiment.id)},
                                   {'title': '%s (%s)' % (page.title, page.name)
                                    if page.title else 'No title (%s)' % page.name,
                                    'url': request.route_url('experiment.page.edit', eid=experiment.id, pid=page.id)},
                                   {'title': 'Data',
                                    'url': request.route_url('experiment.page.data', eid=experiment.id, pid=page.id)}],
                        'errors': e.error_dict,
                        'values': request.params}
        return {'experiment': experiment,
                'page': page,
                'data_sets': data_sets,
                'crumbs': [{'title': 'Experiments',
                            'url': request.route_url('dashboard')},
                           {'title': experiment.title,
                            'url': request.route_url('experiment.view', eid=experiment.id)},
                           {'title': 'Pages',
                            'url': request.route_url('experiment.page', eid=experiment.id)},
                           {'title': '%s (%s)' % (page.title, page.name)
                            if page.title else 'No title (%s)' % page.name,
                            'url': request.route_url('experiment.page.edit', eid=experiment.id, pid=page.id)},
                           {'title': 'Data',
                            'url': request.route_url('experiment.page.data', eid=experiment.id, pid=page.id)}]}
    else:
        raise HTTPNotFound()


class PageSettingsSchema(CSRFSchema):

    name = formencode.Pipe(formencode.validators.UnicodeString(not_empty=True,
                                                               messages={'empty': 'Please provide a unique name'}),
                           PageNameUniqueValidator())
    title = formencode.validators.UnicodeString()
    number_questions = formencode.validators.StringBool(if_missing=False, if_empty=False)
    styles = formencode.validators.UnicodeString()
    scripts = formencode.validators.UnicodeString()


@view_config(route_name='experiment.page.settings', renderer='ess:templates/page/settings.kajiki')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
def settings(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    page = dbsession.query(Page).filter(and_(Page.id == request.matchdict['pid'],
                                             Page.experiment_id == request.matchdict['eid'])).first()
    if experiment and page:
        if request.method == 'POST':
            try:
                params = PageSettingsSchema().to_python(request.params,
                                                        State(request=request,
                                                              dbsession=dbsession,
                                                              experiment=experiment,
                                                              page_id=request.matchdict['pid']))
                with transaction.manager:
                    dbsession.add(page)
                    page.name = params['name']
                    page.title = params['title']
                    page.styles = params['styles']
                    page.scripts = params['scripts']
                    page['number_questions'] = params['number_questions']
                dbsession.add(page)
                dbsession.add(experiment)
                raise HTTPFound(request.route_url('experiment.page.settings', eid=experiment.id, pid=page.id))
            except formencode.Invalid as e:
                return {'experiment': experiment,
                        'page': page,
                        'crumbs': [{'title': 'Experiments',
                                    'url': request.route_url('dashboard')},
                                   {'title': experiment.title,
                                    'url': request.route_url('experiment.view', eid=experiment.id)},
                                   {'title': 'Pages',
                                    'url': request.route_url('experiment.page', eid=experiment.id)},
                                   {'title': '%s (%s)' % (page.title, page.name)
                                    if page.title else 'No title (%s)' % page.name,
                                    'url': request.route_url('experiment.page.edit', eid=experiment.id, pid=page.id)},
                                   {'title': 'Settings',
                                    'url': request.route_url('experiment.page.settings', eid=experiment.id, pid=page.id)}],
                        'values': request.params,
                        'errors': e.error_dict}
        return {'experiment': experiment,
                'page': page,
                'crumbs': [{'title': 'Experiments',
                            'url': request.route_url('dashboard')},
                           {'title': experiment.title,
                            'url': request.route_url('experiment.view', eid=experiment.id)},
                           {'title': 'Pages',
                            'url': request.route_url('experiment.page', eid=experiment.id)},
                           {'title': '%s (%s)' % (page.title, page.name)
                            if page.title else 'No title (%s)' % page.name,
                            'url': request.route_url('experiment.page.edit', eid=experiment.id, pid=page.id)},
                           {'title': 'Settings',
                            'url': request.route_url('experiment.page.settings', eid=experiment.id, pid=page.id)}]}
    else:
        raise HTTPNotFound()


@view_config(route_name='experiment.page.export', renderer='json')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='view')
@require_method('POST')
def export(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    page = dbsession.query(Page).filter(and_(Page.id == request.matchdict['pid'],
                                             Page.experiment_id == request.matchdict['eid'])).first()
    if experiment and page:
        try:
            CSRFSchema().to_python(request.params, State(request=request))
            request.response.headers['Content-Disposition'] = 'attachment; filename=%s.json' % page.name
            return export_jsonapi(page, includes=[(Page, 'questions'), (Question, 'q_type'),
                                                  (QuestionType, 'q_type_group'), (QuestionType, 'parent'),
                                                  (QuestionTypeGroup, 'parent')])
        except formencode.Invalid:
            raise HTTPFound(request.route_url('experiment.page.edit', eid=experiment.id, pid=page.id))
    else:
        raise HTTPNotFound()
