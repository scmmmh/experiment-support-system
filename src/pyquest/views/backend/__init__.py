# -*- coding: utf-8 -*-

def init(config):
    config.add_route('survey', '/surveys')
    config.add_route('survey.new', '/surveys/new')
    config.add_route('survey.import', '/surveys/import')
    config.add_route('survey.view', '/surveys/{sid}')
    config.add_route('survey.edit', '/surveys/{sid}/edit')
    config.add_route('survey.edit.add_notification', '/surveys/{sid}/add_notification')
    config.add_route('survey.edit.delete_notification', '/surveys/{sid}/delete_notification')
    config.add_route('survey.delete', '/surveys/{sid}/delete')
    config.add_route('survey.status', '/surveys/{sid}/status')
    config.add_route('survey.export', '/surveys/{sid}/export')
    config.add_route('survey.export.ext', '/surveys/{sid}/export.{ext}')
    config.add_route('survey.duplicate', '/surveys/{sid}/duplicate')
    config.add_route('survey.data', '/surveys/{sid}/pages/{qsid}/data')
    config.add_route('data.item.new', '/surveys/{sid}/data/{dsid}/item/new')
    config.add_route('data.item.edit', '/surveys/{sid}/data/{dsid}/item/{did}/edit')
    config.add_route('data.item.delete', '/surveys/{sid}/data/{dsid}/item/{did}/delete')
    config.add_route('data.list', '/surveys/{sid}/data/list')
    config.add_route('data.new', '/surveys/{sid}/data/new')
    config.add_route('data.upload', '/surveys/{sid}/data/upload')
    config.add_route('data.view', '/surveys/{sid}/data/{dsid}/view')
    config.add_route('data.edit', '/surveys/{sid}/data/{dsid}/edit')
    config.add_route('data.delete', '/surveys/{sid}/data/{dsid}/delete')
    config.add_route('data.download', '/surveys/{sid}/data/{dsid}/download')
    config.add_route('data.detach', '/surveys/{sid}/data/{dsid}/detach/{qsid}')
    config.add_route('data.attach', '/surveys/{sid}/data/{dsid}/attach/{qsid}')
    config.add_route('data.pcount', '/surveys/{sid}/pcount/{dsid}')
    config.add_route('data.new.permset', '/surveys/{sid}/data/{dsid}/new/permset')
    config.add_route('data.edit.permset', '/surveys/{sid}/data/{dsid}/edit/permset')
    config.add_route('survey.qsheet', '/surveys/{sid}/pages')
    config.add_route('survey.qsheet.new', '/surveys/{sid}/pages/new')
    config.add_route('survey.qsheet.import', '/surveys/{sid}/pages/import')
    config.add_route('survey.qsheet.edit', '/surveys/{sid}/pages/{qsid}/edit')
    config.add_route('survey.qsheet.edit.add_condition', '/surveys/{sid}/pages/{qsid}/add_condition')
    config.add_route('survey.qsheet.edit.delete_condition', '/surveys/{sid}/pages/{qsid}/delete_condition')
    config.add_route('survey.qsheet.edit.add_question', '/surveys/{sid}/pages/{qsid}/add_question')
    config.add_route('survey.qsheet.edit.delete_question', '/surveys/{sid}/pages/{qsid}/delete_question/{qid}')
    config.add_route('survey.qsheet.edit.source', '/surveys/{sid}/pages/{qsid}/edit/source')
    config.add_route('survey.qsheet.delete', '/surveys/{sid}/pages/{qsid}/delete')
    config.add_route('survey.qsheet.view', '/surveys/{sid}/pages/{qsid}/view')
    config.add_route('survey.qsheet.preview', '/surveys/{sid}/pages/{qsid}/preview')
    config.add_route('survey.qsheet.export', '/surveys/{sid}/pages/{qsid}/export')
    config.add_route('survey.qsheet.export.ext', '/surveys/{sid}/pages/{qsid}/export.{ext}')
    config.add_route('survey.preview', '/surveys/{sid}/preview')
    config.add_route('survey.results', '/surveys/{sid}/results')
    config.add_route('survey.results.by_question', '/surveys/{sid}/results/by_question')
    config.add_route('survey.results.by_question.ext', '/surveys/{sid}/results/by_question.{ext}')
    config.add_route('survey.results.by_participant', '/surveys/{sid}/results/by_participant')
    config.add_route('survey.results.by_participant.ext', '/surveys/{sid}/results/by_participant.{ext}')
