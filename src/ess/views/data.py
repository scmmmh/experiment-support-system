import formencode
import transaction

from csv import DictReader
from io import StringIO
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.renderers import render_to_response
from pyramid.view import view_config
from pywebtools.formencode import CSRFSchema, State, CSRFValidator
from pywebtools.pyramid.auth.views import current_user, require_permission
from pywebtools.pyramid.decorators import require_method
from pywebtools.sqlalchemy import DBSession
from sqlalchemy import and_, func

from ess.models import Experiment, DataSet, DataItem
from ess.validators import DataSetUniqueValidator
from pyquest.validation import DynamicSchema


def init(config):
    config.add_route('experiment.data', '/experiments/{eid}/data')
    config.add_route('experiment.data.create', '/experiments/{eid}/data/create')
    config.add_route('experiment.data.upload', '/experiments/{eid}/data/upload')
    config.add_route('experiment.data.view', '/experiments/{eid}/data/{did}')
    config.add_route('experiment.data.edit', '/experiments/{eid}/data/{did}/edit')
    config.add_route('experiment.data.delete', '/experiments/{eid}/data/{did}/delete')
    config.add_route('experiment.data.item.add', '/experiments/{eid}/data/{did}/add')
    config.add_route('experiment.data.item.reorder', '/experiments/{eid}/data/{did}/reorder')
    config.add_route('experiment.data.item.edit', '/experiments/{eid}/data/{did}/{diid}/edit')
    config.add_route('experiment.data.item.delete', '/experiments/{eid}/data/{did}/{diid}/delete')


@view_config(route_name='experiment.data', renderer='ess:templates/data/data_list.kajiki')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='view')
def data_list(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    if experiment:
        return {'experiment': experiment,
                'crumbs': [{'title': 'Experiments',
                            'url': request.route_url('dashboard')},
                           {'title': experiment.title,
                            'url': request.route_url('experiment.view', eid=experiment.id)},
                           {'title': 'Data Sets',
                            'url': request.route_url('experiment.data', eid=experiment.id)}]}
    else:
        raise HTTPNotFound()


class DataSetCreateSchema(CSRFSchema):

    name = DataSetUniqueValidator(not_empty=True)


@view_config(route_name='experiment.data.create', renderer='ess:templates/data/data_create.kajiki')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
def data_create(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    if experiment:
        if request.method == 'POST':
            try:
                params = DataSetCreateSchema().to_python(request.params, State(request=request,
                                                                               dbsession=dbsession,
                                                                               experiment=experiment))
                with transaction.manager:
                    dbsession.add(experiment)
                    data_set = DataSet(name=params['name'],
                                       experiment=experiment,
                                       type='dataset')
                    data_set['columns'] = []
                    dbsession.add(data_set)
                dbsession.add(experiment)
                dbsession.add(data_set)
                raise HTTPFound(request.route_url('experiment.data.edit', eid=experiment.id, did=data_set.id))
            except formencode.Invalid as e:
                return {'experiment': experiment,
                        'crumbs': [{'title': 'Experiments',
                                    'url': request.route_url('dashboard')},
                                   {'title': experiment.title,
                                    'url': request.route_url('experiment.view', eid=experiment.id)},
                                   {'title': 'Data Sets',
                                    'url': request.route_url('experiment.data', eid=experiment.id)},
                                   {'title': 'Add',
                                    'url': request.route_url('experiment.data.create', eid=experiment.id)}],
                        'values': request.params,
                        'errors': e.error_dict}
        return {'experiment': experiment,
                'crumbs': [{'title': 'Experiments',
                            'url': request.route_url('dashboard')},
                           {'title': experiment.title,
                            'url': request.route_url('experiment.view', eid=experiment.id)},
                           {'title': 'Data Sets',
                            'url': request.route_url('experiment.data', eid=experiment.id)},
                           {'title': 'Add',
                            'url': request.route_url('experiment.data.create', eid=experiment.id)}]}
    else:
        raise HTTPNotFound()


class DataSetUploadSchema(CSRFSchema):

    name = DataSetUniqueValidator(not_empty=True)
    source = formencode.validators.FieldStorageUploadConverter(not_empty=True)


@view_config(route_name='experiment.data.upload', renderer='ess:templates/data/data_upload.kajiki')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
def data_upload(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    if experiment:
        if request.method == 'POST':
            try:
                params = DataSetUploadSchema().to_python(request.params, State(request=request,
                                                                               dbsession=dbsession,
                                                                               experiment=experiment))
                with transaction.manager:
                    dbsession.add(experiment)
                    data_set = DataSet(name=params['name'],
                                       experiment=experiment,
                                       type='dataset')
                    reader = DictReader(StringIO(params['source'].file.read().decode('utf-8')))
                    data_set['columns'] = reader.fieldnames
                    dbsession.add(data_set)
                    for idx, line in enumerate(reader):
                        item = DataItem(data_set=data_set,
                                        order=idx)
                        item['values'] = line
                        dbsession.add(item)
                dbsession.add(experiment)
                dbsession.add(data_set)
                raise HTTPFound(request.route_url('experiment.data.view', eid=experiment.id, did=data_set.id))
            except formencode.Invalid as e:
                return {'experiment': experiment,
                        'crumbs': [{'title': 'Experiments',
                                    'url': request.route_url('dashboard')},
                                   {'title': experiment.title,
                                    'url': request.route_url('experiment.view', eid=experiment.id)},
                                   {'title': 'Data Sets',
                                    'url': request.route_url('experiment.data', eid=experiment.id)},
                                   {'title': 'Upload',
                                    'url': request.route_url('experiment.data.upload', eid=experiment.id)}],
                        'values': request.params,
                        'errors': e.error_dict}
        return {'experiment': experiment,
                'crumbs': [{'title': 'Experiments',
                            'url': request.route_url('dashboard')},
                           {'title': experiment.title,
                            'url': request.route_url('experiment.view', eid=experiment.id)},
                           {'title': 'Data Sets',
                            'url': request.route_url('experiment.data', eid=experiment.id)},
                           {'title': 'Upload',
                            'url': request.route_url('experiment.data.upload', eid=experiment.id)}]}
    else:
        raise HTTPNotFound()


class DataSetEditSchema(CSRFSchema):

    name = DataSetUniqueValidator(not_empty=True)
    column = formencode.foreach.ForEach(formencode.validators.UnicodeString())


@view_config(route_name='experiment.data.view', renderer='ess:templates/data/data_view.kajiki')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
def data_view(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    data_set = dbsession.query(DataSet).filter(and_(DataSet.id == request.matchdict['did'],
                                                    DataSet.experiment_id == request.matchdict['eid'])).first()
    if experiment and data_set:
        return {'experiment': experiment,
                'data_set': data_set,
                'crumbs': [{'title': 'Experiments',
                            'url': request.route_url('dashboard')},
                           {'title': experiment.title,
                            'url': request.route_url('experiment.view', eid=experiment.id)},
                           {'title': 'Data Sets',
                            'url': request.route_url('experiment.data', eid=experiment.id)},
                           {'title': data_set.name,
                            'url': request.route_url('experiment.data.view', eid=experiment.id, did=data_set.id)}]}
    else:
        raise HTTPNotFound()


@view_config(route_name='experiment.data.edit', renderer='ess:templates/data/data_edit.kajiki')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
def data_edit(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    data_set = dbsession.query(DataSet).filter(and_(DataSet.id == request.matchdict['did'],
                                                    DataSet.experiment_id == request.matchdict['eid'])).first()
    if experiment and data_set:
        if request.method == 'POST':
            try:
                params = DataSetEditSchema().to_python(request.params, State(request=request,
                                                                             dbsession=dbsession,
                                                                             experiment=experiment,
                                                                             data_set=data_set))
                with transaction.manager:
                    dbsession.add(data_set)
                    data_set.name = params['name']
                    data_set['columns'] = [c.strip() for c in params['column'] if c.strip()]
                dbsession.add(experiment)
                dbsession.add(data_set)
                raise HTTPFound(request.route_url('experiment.data.view', eid=experiment.id, did=data_set.id))
            except formencode.Invalid as e:
                return {'experiment': experiment,
                        'data_set': data_set,
                        'crumbs': [{'title': 'Experiments',
                                    'url': request.route_url('dashboard')},
                                   {'title': experiment.title,
                                    'url': request.route_url('experiment.view', eid=experiment.id)},
                                   {'title': 'Data Sets',
                                    'url': request.route_url('experiment.data', eid=experiment.id)},
                                   {'title': data_set.name,
                                    'url': request.route_url('experiment.data.view', eid=experiment.id, did=data_set.id)},
                                   {'title': 'Edit',
                                    'url': request.route_url('experiment.data.edit', eid=experiment.id, did=data_set.id)}],
                        'values': request.params,
                        'errors': e.error_dict}
        return {'experiment': experiment,
                'data_set': data_set,
                'crumbs': [{'title': 'Experiments',
                            'url': request.route_url('dashboard')},
                           {'title': experiment.title,
                            'url': request.route_url('experiment.view', eid=experiment.id)},
                           {'title': 'Data',
                            'url': request.route_url('experiment.data', eid=experiment.id)},
                           {'title': data_set.name,
                            'url': request.route_url('experiment.data.view', eid=experiment.id, did=data_set.id)},
                           {'title': 'Edit',
                            'url': request.route_url('experiment.data.edit', eid=experiment.id, did=data_set.id)}]}
    else:
        raise HTTPNotFound()


@view_config(route_name='experiment.data.item.add', renderer='json')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
@require_method('POST')
def data_item_add(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    data_set = dbsession.query(DataSet).filter(and_(DataSet.id == request.matchdict['did'],
                                                    DataSet.experiment_id == request.matchdict['eid'])).first()
    if experiment and data_set:
        try:
            schema = DynamicSchema()
            schema.add_field('csrf_token', CSRFValidator())
            for column in data_set['columns']:
                schema.add_field(column, formencode.validators.UnicodeString(if_empty='', if_missing=''))
            params = schema.to_python(request.params, State(request=request))
            with transaction.manager:
                dbsession.add(data_set)
                order = dbsession.query(func.max(DataItem.order)).filter(DataItem.dataset_id == data_set.id).first()
                if order[0] is None:
                    order = 1
                else:
                    order = order[0] + 1
                data_item = DataItem(dataset_id=data_set.id,
                                     order=order)
                data = {}
                for column in data_set['columns']:
                    data[column] = params[column]
                data_item['values'] = data
                dbsession.add(data_item)
            dbsession.add(data_item)
            return {'status': 'ok',
                    'id': data_item.id,
                    'order': data_item.order,
                    'values': data_item['values']}
        except formencode.Invalid as e:
            return {'status': 'error',
                    'errors': e.unpack_errors()}
    else:
        raise HTTPNotFound()


@view_config(route_name='experiment.data.item.edit', renderer='json')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
@require_method('POST')
def data_item_edit(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    data_set = dbsession.query(DataSet).filter(and_(DataSet.id == request.matchdict['did'],
                                                    DataSet.experiment_id == request.matchdict['eid'])).first()
    data_item = dbsession.query(DataItem).filter(and_(DataItem.id == request.matchdict['diid'],
                                                      DataItem.dataset_id == request.matchdict['did'])).first()
    if experiment and data_set and data_item:
        try:
            schema = DynamicSchema()
            schema.add_field('csrf_token', CSRFValidator())
            for column in data_set['columns']:
                schema.add_field(column, formencode.validators.UnicodeString(if_empty='', if_missing=''))
            params = schema.to_python(request.params, State(request=request))
            with transaction.manager:
                dbsession.add(data_item)
                dbsession.add(data_set)
                data = {}
                for column in data_set['columns']:
                    data[column] = params[column]
                data_item['values'] = data
            dbsession.add(data_item)
            return {'status': 'ok',
                    'id': data_item.id,
                    'order': data_item.order,
                    'values': data_item['values']}
        except formencode.Invalid as e:
            return {'status': 'error',
                    'errors': e.unpack_errors()}
        dbsession.add(experiment)
        dbsession.add(data_set)
        dbsession.add(data_item)
        raise HTTPFound(request.route_url('experiment.data.view', eid=experiment.id, did=data_set.id))
    else:
        raise HTTPNotFound()


@view_config(route_name='experiment.data.item.delete', renderer='json')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
@require_method('POST')
def data_item_delete(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    data_set = dbsession.query(DataSet).filter(and_(DataSet.id == request.matchdict['did'],
                                                    DataSet.experiment_id == request.matchdict['eid'])).first()
    data_item = dbsession.query(DataItem).filter(and_(DataItem.id == request.matchdict['diid'],
                                                      DataItem.dataset_id == request.matchdict['did'])).first()
    if experiment and data_set and data_item:
        with transaction.manager:
            dbsession.delete(data_item)
        dbsession.add(experiment)
        dbsession.add(data_set)
        raise HTTPFound(request.route_url('experiment.data.view', eid=experiment.id, did=data_set.id))
    else:
        raise HTTPNotFound()


class ReorderSchema(CSRFSchema):

    item = formencode.foreach.ForEach(formencode.validators.Int, convert_to_list=True)


@view_config(route_name='experiment.data.item.reorder', renderer='json')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
@require_method('POST')
def data_reorder(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    data_set = dbsession.query(DataSet).filter(and_(DataSet.id == request.matchdict['did'],
                                                    DataSet.experiment_id == request.matchdict['eid'])).first()
    if experiment and data_set:
        try:
            params = ReorderSchema().to_python(request.params, State(request=request))
            with transaction.manager:
                for idx, qid in enumerate(params['item']):
                    item = dbsession.query(DataItem).filter(and_(DataItem.id == qid,
                                                                 DataItem.dataset_id == data_set.id)).first()
                    if item is not None:
                        item.order = idx
            return {'status': 'ok'}
        except formencode.Invalid:
            return {'status': 'error'}
    else:
        raise HTTPNotFound()


@view_config(route_name='experiment.data.delete', renderer='json')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
@require_method('POST')
def data_delete(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    data_set = dbsession.query(DataSet).filter(and_(DataSet.id == request.matchdict['did'],
                                                    DataSet.experiment_id == request.matchdict['eid'])).first()
    if experiment and data_set:
        try:
            CSRFSchema().to_python(request.params, State(request=request))
            with transaction.manager:
                dbsession.delete(data_set)
            dbsession.add(experiment)
            raise HTTPFound(request.route_url('experiment.data', eid=experiment.id))
        except formencode.Invalid:
            raise HTTPFound(request.route_url('experiment.data.view', eid=experiment.id, did=data_set.id))
    else:
        raise HTTPNotFound()
