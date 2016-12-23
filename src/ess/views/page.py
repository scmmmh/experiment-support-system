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

from ess.models import Experiment, Page, QuestionTypeGroup, Question, QuestionType
from ess.validators import PageNameUniqueValidator, QuestionEditSchema


def init(config):
    config.add_route('experiment.page', '/experiments/{eid}/pages')
    config.add_route('experiment.page.create', '/experiments/{eid}/pages/create')
    config.add_route('experiment.page.edit', '/experiments/{eid}/pages/{pid}')
    config.add_route('experiment.page.edit.add_question', '/experiments/{eid}/pages/{pid}/add_question/{qtid}')
    config.add_route('experiment.page.edit.question', '/experiments/{eid}/pages/{pid}/questions/{qid}/edit')
    config.add_route('experiment.page.edit.reorder', '/experiments/{eid}/pages/{pid}/reorder')
    config.add_route('experiment.page.delete.question', '/experiments/{eid}/pages/{pid}/questions/{qid}/delete')


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
                dbsession.add(question)
            dbsession.add(experiment)
            dbsession.add(page)
            dbsession.add(question)
            data = render_to_response('ess:templates/page/edit_question.kajiki',
                                                   {'experiment': experiment,
                                                    'page': page,
                                                    'question': question},
                                                   request=request)
            return {'status': 'ok',
                    'question': data.body.decode('utf-8')}
        except formencode.Invalid as e:
            return {'status': 'error',
                    'errors': e.unpack_errors()}
    else:
        raise HTTPNotFound()


class ReorderPageSchema(CSRFSchema):

    question = formencode.foreach.ForEach(formencode.validators.Int, convert_to_list=True)


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
            params = ReorderPageSchema().to_python(request.params, State(request=request))
            with transaction.manager:
                for idx, qid in enumerate(params['question']):
                    question = dbsession.query(Question).filter(and_(Question.id == qid,
                                                                     Question.page == page)).first()
                    if question is not None:
                        question.order = idx
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
