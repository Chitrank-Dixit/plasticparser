# -*- coding: utf-8 -*-
RESERVED_CHARS = ('\\', '+', '-', '&&',
                  '||', '!', '(', ')',
                  '{', '}', '[', ']',
                  '^', '"', '~', '*',
                  '?', '/', ':')

ESCAPE_CHARS = ('\\', '+', '-', '&&',
                '||', '!',
                '{', '}', '[', ']',
                '^', '"', '~', '*',
                '?', '/')

COMPARISON_OPERATORS = ('>', '<', '<=', '>=')


def _sanitize_term_value(value):
    if not isinstance(value, basestring):
        return value
    for char in RESERVED_CHARS:
        value = value.replace(char, u'\{}'.format(char))
    return value


def _escape_input_query(value):
    if not isinstance(value, basestring):
        return value
    for char in ESCAPE_CHARS:
        value = value.replace(char, u'\{}'.format(char))
    return value


class Entity(object):
    def __eq__(self, other):
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        return False

    def __ne__(self, other):
        return not self.__eq__(other)


class Filter(Entity):
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def get_query(self):
        clause = "terms" if isinstance(self.value, list) else "term"
        return {
            clause: {
                self.key: self.value
            }
        }


class TypeFilter(Filter):
    def __init__(self, value):
        Filter.__init__(self, 'type', value)

    def get_query(self):
        return {
            "type": {
                "value": self.value
            }
        }


class Filters(Entity):
    def __init__(self, token_list=None, type_filters=None):
        self.token_list = token_list
        self.type_filters = type_filters if type_filters else []

    def _get_logical_query(self, logical_type):
        filter_list = []
        if self.token_list:
            filter_list = [Filter(*token.popitem()).get_query() for token in self.token_list.get(logical_type, [])]
        if self.type_filters and logical_type == 'and':
            filter_list.append(self.type_filters[0].get_query())

        return filter_list

    def get_query(self):
        return {
            'must': self._get_logical_query('and'),
            'should': self._get_logical_query('or'),
            'must_not': self._get_logical_query('not'),
        }


class Query(Entity):
    def __init__(self, query):
        self.query = _escape_input_query(query)

    def get_query(self):
        return {
            "query_string": {
                "query": self.query

            }
        }


class Expression(Entity):
    def __init__(self, type_filter, query, filters=None):
        self.type_filter = type_filter
        self.query = query
        type_filters = [type_filter] if type_filter else []
        if filters:
            filters.type_filters = type_filters
            self.filters = filters
        else:
            self.filters = Filters(type_filters=type_filters) if type_filters else None

    def get_query(self):
        return {
            "query": {
                "filtered": {
                    "query": self.query.get_query(),
                    "filter": {"bool": self.filters.get_query()}
                }
            }
        }

