# -*- coding: utf-8 -*-

def init(config):
    config.add_route('survey', '/surveys')
    config.add_route('survey.new', '/surveys/new')
    config.add_route('survey.import', '/surveys/import')
    config.add_route('survey.view', '/surveys/{sid}')
    config.add_route('survey.edit', '/surveys/{sid}/edit')
    config.add_route('survey.delete', '/surveys/{sid}/delete')
    config.add_route('survey.status', '/surveys/{sid}/status')
    config.add_route('survey.export', '/surveys/{sid}/export')
    config.add_route('survey.export.ext', '/surveys/{sid}/export.{ext}')
    config.add_route('survey.duplicate', '/surveys/{sid}/duplicate')
    config.add_route('survey.data', '/surveys/{sid}/pages/{qsid}/data')
    config.add_route('dataitem.new', '/dataitem/{disid}/new')
    config.add_route('dataitem.edit', '/dataitem/{did}/edit')
    config.add_route('dataitem.delete', '/dataitem/{did}/delete')
    config.add_route('dataset.list', '/dataset/list')
    config.add_route('dataset.new', '/dataset/new')
    config.add_route('dataset.upload', '/dataset/upload')
    config.add_route('dataset.view', '/dataset/{disid}')
    config.add_route('dataset.edit', '/dataset/{disid}/edit')
    config.add_route('dataset.delete', '/dataset/{disid}/delete')
    config.add_route('dataset.download', '/dataset/{disid}/download')
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
    config.add_route('survey.qsheet.export', '/surveys/{sid}/pages/{qsid}/export')
    config.add_route('survey.qsheet.export.ext', '/surveys/{sid}/pages/{qsid}/export.{ext}')
    config.add_route('survey.preview', '/surveys/{sid}/preview')
    config.add_route('survey.results', '/surveys/{sid}/results')
    config.add_route('survey.results.by_question', '/surveys/{sid}/results/by_question')
    config.add_route('survey.results.by_question.ext', '/surveys/{sid}/results/by_question.{ext}')
    config.add_route('survey.results.by_participant', '/surveys/{sid}/results/by_participant')
    config.add_route('survey.results.by_participant.ext', '/surveys/{sid}/results/by_participant.{ext}')
