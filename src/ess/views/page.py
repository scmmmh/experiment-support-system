import formencode
import transaction

from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.renderers import render_to_response
from pyramid.view import view_config
from pywebtools.formencode import CSRFSchema, State
from pywebtools.pyramid.auth.views import current_user, require_permission
from pywebtools.sqlalchemy import DBSession
from sqlalchemy import and_

from ess.models import Experiment, Page, QuestionTypeGroup, Question
from ess.validators import PageNameUniqueValidator, QuestionEditSchema


def init(config):
    config.add_route('experiment.page', '/experiments/{eid}/pages')
    config.add_route('experiment.page.create', '/experiments/{eid}/pages/create')
    config.add_route('experiment.page.edit', '/experiments/{eid}/pages/{pid}')
    config.add_route('experiment.page.edit.question', '/experiments/{eid}/pages/{pid}/questions/{qid}')


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
                raise HTTPFound(request.route_url('experiment.page.view', eid=experiment.id, pid=page.id))
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
def view(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    if experiment:
        page = dbsession.query(Page).filter(and_(Page.id == request.matchdict['pid'],
                                                 Page.experiment == experiment)).first()
    else:
        page = None
    if experiment and page:
        qgroups = dbsession.query(QuestionTypeGroup).filter(QuestionTypeGroup.parent_id == None).order_by(QuestionTypeGroup.order)
        return {'experiment': experiment,
                'page': page,
                'qgroups': qgroups,
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
            params = QuestionEditSchema(question).to_python(request.params, State(request=request,
                                                                                  dbsession=dbsession))
            with transaction.manager:
                for key, value in params.items():
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
