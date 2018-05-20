# -*- coding: utf-8 -*-
# Copyright (c) 2018 Christiaan Frans Rademan.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holders nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
# THE POSSIBILITY OF SUCH DAMAGE.
from math import ceil
from operator import itemgetter

from luxon import g
from luxon import db
from luxon.utils.sql import build_where, build_like
from luxon.utils.cast import to_list
from luxon import SQLModel
from luxon.exceptions import AccessDeniedError


def raw_list(req, data, limit=None, rows=None):
    # Step 1 Build Pages
    if limit is None:
        limit = int(req.query_params.get('limit', 10))

    page = int(req.query_params.get('page', 1)) - 1
    if rows is None:
        start = page * limit
        end = start + 10

    searches = to_list(req.query_params.get('search'))

    # Step 2 Build Data Payload
    result = []
    search_query = ''
    for row in data:
        if ('domain' in row and
                req.context_domain is not None):
            if row['domain'] != req.context_domain:
                continue
        if ('tenant_id' in row and
                req.context_tenant_id is not None):
            if row['tenant_id'] != req.context_tenant_id:
                continue
        for search in searches:
            search_query += '&search=%s' % search
            try:
                search_field, value = search.split(':')
            except (TypeError, ValueError):
                raise ValueError("Invalid field search field value." +
                                 " Expecting 'field:value'")
            try:
                if value not in row[search_field]:
                    continue
            except KeyError:
                raise ValueError("Unknown field '%s' in search" %
                                 search_field)

        result.append(row)

    # Step 3 Sort though data
    sort = to_list(req.query_params.get('sort'))
    sort_query = ''
    for order in sort:
        sort_query = '&sort=%s' % order
        try:
            order_field, order_type = order.split(':')
        except (TypeError, ValueError):
            raise ValueError("Invalid field sort field value." +
                             " Expecting 'field:desc' or 'field:asc'")

        if len(data) > 0:
            order_type = order_type.lower()
            # Check if field to order by is valid.
            if order_field not in data[0]:
                raise ValueError("Unknown field '%s' in sort" %
                                 order_field)

            # Sort field desc/asc
            if order_type == 'desc':
                result = list(sorted(result, key=itemgetter(order_field),
                                     reverse=True))
            elif order_type == 'asc':
                result = list(sorted(result, key=itemgetter(order_field)))
            else:
                raise ValueError('Bad order for sort provided')

    # Step 4 Limit rows based on pages.
    if rows is None:
        result = result[start:end]

    # Step 5 Build links next &/ /previous
    links = {}
    if g.app.config.get('application', 'use_forwarded') is True:
        resource = (req.forwarded_scheme + "://" +
                    req.forwarded_host +
                    req.app + req.route)
    else:
        resource = (req.scheme + "://" +
                    req.netloc +
                    req.app + req.route)

    if page + 1 > 1:
        links['previous'] = resource + '?limit=%s&page=%s' % (limit, page,)
        links['previous'] += sort_query
        links['previous'] += search_query

    if page + 1 < ceil(rows / limit):
        links['next'] = resource + '?limit=%s&page=%s' % (limit, page + 2,)
        links['next'] += sort_query
        links['next'] += search_query

    # Step 6 Finally return result
    return {
        'links': links,
        'payload': result,
        'metadata': {
            "records": rows,
            "page": page + 1,
            "pages": ceil(rows / limit),
            "per_page": limit,
            "sort": sort,
            "search": searches,
        }
    }


def sql_list(req, table, fields, limit=None, **kwargs):
    # Step 1 Build sort
    sort_range_query = None
    sort = to_list(req.query_params.get('sort'))
    if len(sort) > 0:
        ordering = []
        for order in sort:
            try:
                order_field, order_type = order.split(':')
            except (TypeError, ValueError):
                raise ValueError("Invalid field sort field value." +
                                 " Expecting 'field:desc' or 'field:asc'")
            order_type = order_type.lower()
            if order_type != "asc" and order_type != "desc":
                raise ValueError('Bad order for sort provided')
            if order_field not in fields:
                raise ValueError("Unknown field '%s' in sort" %
                                 order_field)
            ordering.append("%s %s" % (order_field, order_type))

        sort_range_query = " ORDER BY %s" % ','.join(ordering)

    # Step 2 Build Pages
    if limit is None:
        limit = int(req.query_params.get('limit', 10))

    page = int(req.query_params.get('page', 1)) - 1
    start = page * limit
    limit_range_query = " LIMIT %s, %s" % (start, limit,)

    # Step 3 Search
    search_query = {}
    searches = to_list(req.query_params.get('search'))
    for search in searches:
        try:
            search_field, value = search.split(':')
        except (TypeError, ValueError):
            raise ValueError("Invalid field search field value." +
                             " Expecting 'field:value'")
        if search_field not in fields:
            raise ValueError("Unknown field '%s' in search" %
                             search_field)
        search_query[search_field] = value

    # Step 4 Prepre to run queries
    fields_str = ", ".join(fields)
    context_query = {}
    context_query.update(kwargs)

    with db() as conn:
        if (conn.has_field(table, 'domain') and
                req.context_domain is not None):
            from luxom import GetLogger
            log = GetLogger()
            log.critical('boom')
            context_query['domain'] = req.context_domain

        if (conn.has_field(table, 'tenant_id') and
                req.context_tenant_id is not None):
            context_query['tenant_id'] = req.context_tenant_id

        where, values = build_where(**context_query)
        search_where, search_values = build_like(**search_query)

        # Step 5 we get the total_rows
        sql = 'SELECT count(id) as total FROM %s' % table

        if where != '' or search_where != '':
            sql += " WHERE "

        if where != '':
            sql += " " + where

        if where != '' and search_where != '':
            sql += " AND "

        if search_where != '':
            sql += " " + search_where

        result = conn.execute(sql,
                              values + search_values).fetchone()
        if result:
            rows = result['total']
        else:
            rows = 0

        # Step 6 we get the data
        sql = 'SELECT %s FROM %s' % (fields_str, table,)

        if where != '' or search_where != '':
            sql += " WHERE "

        if where != '':
            sql += " " + where

        if where != '' and search_where != '':
            sql += " AND "

        if search_where != '':
            sql += " " + search_where

        if sort_range_query:
            sql += sort_range_query

        sql += limit_range_query

        result = conn.execute(sql,
                              values + search_values).fetchall()

    # Step 7 we pass it to standard list output provider
    return raw_list(req, result, limit=limit, rows=rows)


def obj(req, ModelClass, sql_id=None, hide=None):
    model = ModelClass(hide=hide)
    if issubclass(ModelClass, SQLModel) and sql_id:
        model.sql_id(sql_id)

    fields = ModelClass.fields
    if ('domain' in fields and
            req.credentials.domain and
            req.credentials.domain != model['domain']):
        raise AccessDeniedError('object not in context domain')
    if ('tenant_id' in fields and
            req.credentials.tenant_id and
            req.credentials.tenant_id != model['tenant_id']):
        raise AccessDeniedError('object not in context tenant')

    if req.method in ['POST', 'PATCH', 'PUT']:
        create = req.json.copy()
        if ('domain' in fields):
            if req.credentials.domain:
                create.update({"domain": req.credentials.domain})
        if ('tenant_id' in fields):
            if req.credentials.tenant_id:
                create.update({"tenant_id": req.credentials.tenant_id})
        model.update(create)
    elif (req.method == 'DELETE' and
            issubclass(ModelClass, SQLModel) and
            sql_id):
        model.delete()

    return model
