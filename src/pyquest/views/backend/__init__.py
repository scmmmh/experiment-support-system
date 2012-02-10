# -*- coding: utf-8 -*-

def init(config):
    config.add_route('survey', '/surveys')
    config.add_route('survey.new', '/surveys/new')
    config.add_route('survey.view', '/surveys/{sid}')
    config.add_route('survey.edit', '/surveys/{sid}/edit')
    config.add_route('survey.delete', '/surveys/{sid}/delete')
    config.add_route('survey.data', '/surveys/{sid}/data')
    config.add_route('survey.data.upload', '/surveys/{sid}/data/upload')
    config.add_route('survey.data.new', '/surveys/{sid}/data/new')
    config.add_route('survey.data.edit', '/surveys/{sid}/data/{did}/edit')
    config.add_route('survey.data.delete', '/surveys/{sid}/data/{did}/delete')
    config.add_route('survey.data.clear', '/surveys/{sid}/data/clear')
    config.add_route('survey.qsheet', '/surveys/{sid}/pages')
    config.add_route('survey.qsheet.new', '/surveys/{sid}/pages/new')
    config.add_route('survey.qsheet.edit', '/surveys/{sid}/pages/{qsid}/edit')
    config.add_route('survey.qsheet.delete', '/surveys/{sid}/pages/{qsid}/delete')
    config.add_route('survey.qsheet.preview', '/surveys/{sid}/pages/{qsid}/preview')
    config.add_route('survey.preview', '/surveys/{sid}/preview')
    config.add_route('survey.results', '/surveys/{sid}/results')
    config.add_route('survey.results.download', '/surveys/{sid}/results/download')