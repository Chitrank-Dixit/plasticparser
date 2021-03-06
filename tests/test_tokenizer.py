import unittest

from plasticparser import tokenizer, grammar_parsers


class TokenizerTest(unittest.TestCase):
    def test_should_sanitize_value(self):
        for char in grammar_parsers.RESERVED_CHARS:
            if char not in '(':
                sanitized_value = grammar_parsers.sanitize_value(
                    "abc{}".format(char))
                self.assertEqual(sanitized_value, 'abc\\{}'.format(char))

    def get_query_string(self, parsed_dict):
        return parsed_dict['query']['filtered'][
            'query']['query_string']['query']

    def test_should_tokenize_and_parse_logical_expression(self):
        query_string = "abc:>def"
        parsed_string = tokenizer.tokenize(query_string)
        self.assertEqual(self.get_query_string(parsed_string), "abc:>def")

        query_string = "abc:>def and mms:>asd"
        parsed_string = tokenizer.tokenize(query_string)
        self.assertEqual(
            self.get_query_string(parsed_string),
            "abc:>def AND mms:>asd")

        query_string = "abc:>def mms:>asd"
        parsed_string = tokenizer.tokenize(query_string)
        self.assertEqual(
            self.get_query_string(parsed_string),
            "abc:>def mms:>asd")

        query_string = "(abc:>def mms:>asd)"
        parsed_string = tokenizer.tokenize(query_string)
        self.assertEqual(
            self.get_query_string(parsed_string),
            "(abc:>def mms:>asd)")

        query_string = "abc:>def mms:>asd (abc:def or pqe:123) and blab:blab"
        parsed_string = tokenizer.tokenize(query_string)
        self.assertEqual(
            self.get_query_string(parsed_string),
            "abc:>def mms:>asd (abc:def OR pqe:123) AND blab:blab")

        query_string = "( abc:>def mms:>asd ) (abc:>def mms:>asd) "
        parsed_string = tokenizer.tokenize(query_string)
        self.assertEqual(
            self.get_query_string(parsed_string),
            "(abc:>def mms:>asd) (abc:>def mms:>asd)")

        query_string = "( abc:>def mms:>asd ) and (abc:>def mms:>asd) "
        parsed_string = tokenizer.tokenize(query_string)
        self.assertEqual(
            self.get_query_string(parsed_string),
            "(abc:>def mms:>asd) AND (abc:>def mms:>asd)")

        query_string = "abc def"
        parsed_string = tokenizer.tokenize(query_string)
        self.assertEqual(self.get_query_string(parsed_string), "abc def")

        query_string = 'abc (python or london) (abc:def dd:ff) [fgdgdfg]'
        parsed_string = tokenizer.tokenize(query_string)
        self.assertEqual(
            self.get_query_string(parsed_string),
            u'abc (python OR london) (abc:def dd:ff) \[fgdgdfg\]')

    def test_should_parse_logical_expression_with_type_and_facets(self):
        query_string = "type:def facets: [ aaa(abc:def) ] (abc:>def mms:>asd)"
        parsed_string = tokenizer.tokenize(query_string)
        expected_query_string = {
            'query': {
                'filtered': {
                    'filter': {
                        'bool': {
                            'should': [], 'must_not': [], 'must': [
                            {
                                'type': {
                                    'value': 'def'}}]}}, 'query': {
                    'query_string': {
                        'query': u'(abc:>def mms:>asd)',
                        "default_operator": "and"}}}},
            'facets': {
                'aaa': {
                    'facet_filter': {
                        'query': {
                            'query_string': {
                                'query': u'abc:def', "default_operator": "and"}}}, 'terms': {
                    'field': 'aaa_nonngram', 'size': 20}}}}

        self.assertEqual(parsed_string, expected_query_string)

    def test_should_parse_logical_expression_with_type(self):
        query_string = "type:def (abc:>def mms:>asd)"
        parsed_string = tokenizer.tokenize(query_string)
        expected_query_string = {
            'query': {
                'filtered': {
                    'filter': {
                        'bool': {
                            'should': [],
                            'must_not': [],
                            'must': [
                                {
                                    'type': {
                                        'value': 'def'}}]}},
                    'query': {
                        'query_string': {
                            'query': u'(abc:>def mms:>asd)',
                            "default_operator": "and"}}}},
        }
        self.assertEqual(parsed_string, expected_query_string)

    def test_should_parse_logical_expression_with_type_multi_facets(self):
        query_string = "type:def (abc:>def mms:>asd)    facets: [ aaa.bb(abc:def) bbb(cc:ddd) ] "
        parsed_string = tokenizer.tokenize(query_string)
        expected_query_string = {
            'query': {
                'filtered': {
                    'filter': {
                        'bool': {
                            'should': [], 'must_not': [], 'must': [
                            {
                                'type': {
                                    'value': 'def'}}]}}, 'query': {
                    'query_string': {
                        'query': u'(abc:>def mms:>asd)',
                        "default_operator": "and"}}}},
            'facets': {
                'aaa.bb': {
                    'facet_filter': {
                        'query': {
                            'query_string': {
                                'query': u'abc:def', "default_operator": "and"}}}, 'terms': {
                    'field': 'bb_nonngram', 'size': 20}, 'nested': u'aaa'},
                'bbb': {
                    'facet_filter': {
                        'query': {
                            'query_string': {
                                'query': u'cc:ddd', "default_operator": "and"}}}, 'terms': {
                    'field': 'bbb_nonngram', 'size': 20}}}}
        self.assertEqual(parsed_string, expected_query_string)

    def test_should_parse_basic_logical_expression(self):
        query_string = 'title:hello OR description:"world"'
        parsed_string = tokenizer.tokenize(query_string)
        expected_query_string = {
            'query': {
                'filtered': {
                    'filter': {
                        'bool': {
                            'should': [],
                            'must_not': [],
                            'must': []}},
                    'query': {
                        'query_string': {
                            'query': u'title:hello OR description:"world"',
                            "default_operator": "and"}}}},
        }
        self.assertEqual(parsed_string, expected_query_string)

    def test_should_parse_basic_logical_expression_facets_with_no_facet_filters(
            self):
        query_string = "type:def (abc:>def mms:>asd) facets: [ aaa.bb ]"
        parsed_string = tokenizer.tokenize(query_string)
        self.assertEqual(
            parsed_string, {'query': {
                'filtered': {'filter': {'bool': {'should': [], 'must_not': [], 'must': [{'type': {'value': 'def'}}]}},
                             'query': {'query_string': {'query': u'(abc:>def mms:>asd)', 'default_operator': 'and'}}}},
                            'facets': {'aaa.bb': {'terms': {'field': 'bb_nonngram', 'size': 20}}}})

    def test_should_parse_basic_logical_expression_facets_with_simple_field(
            self):
        query_string = "type:def (abc:>def mms:>asd) facets: [ aaa ]"
        parsed_string = tokenizer.tokenize(query_string)
        self.assertEqual(
            parsed_string, {
                'query': {
                    'filtered': {
                        'filter': {
                            'bool': {
                                'should': [], 'must_not': [], 'must': [
                                {
                                    'type': {
                                        'value': 'def'}}]}}, 'query': {
                        'query_string': {
                            'query': u'(abc:>def mms:>asd)',
                            "default_operator": "and"}}}},
                'facets': {
                    'aaa': {
                        'terms': {
                            'field': 'aaa_nonngram', 'size': 20}}}})

    def test_should_parse_multiword_field_value(self):
        query_string = "name:(krace OR kumar) abc:>def"
        parsed_string = tokenizer.tokenize(query_string)
        self.assertEqual(parsed_string['query']['filtered']['query']['query_string']['query'],
                         u'name:(krace OR kumar) abc:>def')

    def test_should_parse_logical_expression_with_type_and_facets_2(self):
        query_string = "facets: [aaa(a:b abc:(def fff) c:d e:(f))]"
        parsed_string = tokenizer.tokenize(query_string)
        expected_parse_string = {
            'query': {'filtered': {'filter': {'bool': {'should': [], 'must_not': [], 'must': []}}}}, 'facets': {
            'aaa': {'facet_filter': {
            'query': {'query_string': {'query': u'a:b abc:(def fff) c:d e:(f)', "default_operator": "and"}}},
                    'terms': {'field': 'aaa_nonngram', 'size': 20}}}}
        self.assertEqual(parsed_string, expected_parse_string)

    def test_should_parse_nested_expression(self):
        query_string = "nested:[aaa(a:(bb) abc:(def fff))]"
        parsed_string = tokenizer.tokenize(query_string)
        self.assertEqual(parsed_string, {'query': {'filtered': {'filter': {'bool': {'should': [], 'must_not': [],
                                                                                    'must': [{'nested': {'path': 'aaa',
                                                                                                         'query': {
                                                                                                         'query_string': {
                                                                                                         'query': u'a:(bb) abc:(def fff)',
                                                                                                         'default_operator': 'and'}}}}]}}}},
                                         })

    def test_should_escape_value_with_colon(self):
        query_string = "tags:dev:ops"
        parsed_string = tokenizer.tokenize(query_string)
        self.assertEqual(parsed_string['query']['filtered']['query']['query_string']['query'],
                         u'tags:dev\:ops')