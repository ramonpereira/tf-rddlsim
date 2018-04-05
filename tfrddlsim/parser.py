from ply import lex, yacc

from tfrddlsim.rddl import RDDL, Domain, Instance, NonFluents
from tfrddlsim.pvariable import NonFluent, StateFluent


alpha = r'[A-Za-z]'
digit = r'[0-9]'
idenfifier = r'(' + alpha + r')((' + alpha + r'|' + digit + r'|\-|\_)*(' + alpha + r'|' + digit + r'))?(\')?'
integer = digit + r'+'
double = digit + r'*\.' + digit + r'+'
variable = r'\?(' + alpha + r'|' + digit + r'|\-|\_)*(' + alpha + r'|' + digit + r')'
enum_value = r'\@(' + alpha + r'|' + digit + r'|\-|\_)*(' + alpha + r'|' + digit + r')'


class RDDLlex(object):

    def __init__(self):
        self.reserved = {
            'domain': 'DOMAIN',
            'instance': 'INSTANCE',
            'horizon': 'HORIZON',
            'discount': 'DISCOUNT',
            'objects': 'OBJECTS',
            'init-state': 'INIT_STATE',
            'requirements': 'REQUIREMENTS',
            'state-action-constraints': 'STATE_ACTION_CONSTRAINTS',
            'action-preconditions': 'ACTION_PRECONDITIONS',
            'state-invariants': 'STATE_INVARIANTS',
            'types': 'TYPES',
            'object': 'OBJECT',
            'bool': 'BOOL',
            'int': 'INT',
            'real': 'REAL',
            'neg-inf': 'NEG_INF',
            'pos-inf': 'POS_INF',
            'pvariables': 'PVARIABLES',
            'non-fluent': 'NON_FLUENT',
            'non-fluents': 'NON_FLUENTS',
            'state-fluent': 'STATE',
            'interm-fluent': 'INTERMEDIATE',
            'derived-fluent': 'DERIVED_FLUENT',
            'observ-fluent': 'OBSERVATION',
            'action-fluent': 'ACTION',
            'level': 'LEVEL',
            'default': 'DEFAULT',
            'max-nondef-actions': 'MAX_NONDEF_ACTIONS',
            'terminate-when': 'TERMINATE_WHEN',
            'terminal': 'TERMINAL',
            'cpfs': 'CPFS',
            'cdfs': 'CDFS',
            'reward': 'REWARD',
            'forall': 'FORALL',
            'exists': 'EXISTS',
            'true': 'TRUE',
            'false': 'FALSE',
            'if': 'IF',
            'then': 'THEN',
            'else': 'ELSE',
            'switch': 'SWITCH',
            'case': 'CASE',
            'otherwise': 'OTHERWISE',
            'KronDelta': 'KRON_DELTA',
            'DiracDelta': 'DIRAC_DELTA',
            'Uniform': 'UNIFORM',
            'Bernoulli': 'BERNOULLI',
            'Discrete': 'DISCRETE',
            'Normal': 'NORMAL',
            'Poisson': 'POISSON',
            'Exponential': 'EXPONENTIAL',
            'Weibull': 'WEIBULL',
            'Gamma': 'GAMMA',
            'Multinomial': 'MULTINOMIAL',
            'Dirichlet': 'DIRICHLET'
        }

        self.tokens = [
            'IDENT',
            'VAR',
            'ENUM_VAL',
            'INTEGER',
            'DOUBLE',
            'AND',
            'OR',
            'NOT',
            'PLUS',
            'TIMES',
            'LPAREN',
            'RPAREN',
            'LCURLY',
            'RCURLY',
            'DOT',
            'COMMA',
            'UNDERSCORE',
            'LBRACK',
            'RBRACK',
            'IMPLY',
            'EQUIV',
            'NEQ',
            'LESSEQ',
            'LESS',
            'GREATEREQ',
            'GREATER',
            'ASSIGN_EQUAL',
            'COMP_EQUAL',
            'DIV',
            'MINUS',
            'COLON',
            'SEMI',
            'DOLLAR_SIGN',
            'QUESTION',
            'AMPERSAND'
        ]
        self.tokens += list(self.reserved.values())

    t_ignore = ' \t'

    t_AND = r'\^'
    t_OR = r'\|'
    t_NOT = r'~'
    t_PLUS = r'\+'
    t_TIMES = r'\*'
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_LCURLY = r'\{'
    t_RCURLY = r'\}'
    t_DOT = r'\.'
    t_COMMA = r'\,'
    t_UNDERSCORE = r'\_'
    t_LBRACK = r'\['
    t_RBRACK = r'\]'
    t_IMPLY = r'=>'
    t_EQUIV = r'<=>'
    t_NEQ = r'~='
    t_LESSEQ = r'<='
    t_LESS = r'<'
    t_GREATEREQ = r'>='
    t_GREATER = r'>'
    t_ASSIGN_EQUAL = r'='
    t_COMP_EQUAL = r'=='
    t_DIV = r'/'
    t_MINUS = r'-'
    t_COLON = r':'
    t_SEMI = r';'
    t_DOLLAR_SIGN = r'\$'
    t_QUESTION = r'\?'
    t_AMPERSAND = r'\&'

    def t_newline(self, t):
        r'\n+'
        self._lexer.lineno += len(t.value)

    def t_COMMENT(self, t):
        r'//[^\r\n]*'
        pass

    @lex.TOKEN(idenfifier)
    def t_IDENT(self, t):
        t.type = self.reserved.get(t.value, 'IDENT')
        return t

    @lex.TOKEN(variable)
    def t_VAR(self, t):
        return t

    @lex.TOKEN(enum_value)
    def t_ENUM_VAL(self, t):
        return t

    @lex.TOKEN(double)
    def t_DOUBLE(self, t):
        t.value = float(t.value)
        return t

    @lex.TOKEN(integer)
    def t_INTEGER(self, t):
        t.value = int(t.value)
        return t

    def t_error(self, t):
        print("Illegal character: {} at line {}".format(t.value[0], self._lexer.lineno))
        t.lexer.skip(1)

    def build(self, **kwargs):
        self._lexer = lex.lex(object=self, **kwargs)

    def input(self, data):
        if self._lexer is None:
            self.build()
        self._lexer.input(data)

    def token(self):
        return self._lexer.token()

    def __call__(self):
        while True:
            tok = self.token()
            if not tok:
                break
            yield tok


class RDDLParser(object):

    def __init__(self, lexer=None):
        if lexer is None:
            self.lexer = RDDLlex()
            self.lexer.build()

        self.tokens = self.lexer.tokens

    def p_rddl(self, p):
        '''rddl : rddl_block'''
        p[0] = RDDL(p[1])

    def p_rddl_block(self, p):
        '''rddl_block : rddl_block domain_block
                      | rddl_block instance_block
                      | rddl_block nonfluent_block
                      | empty'''
        if p[1] is None:
            p[0] = dict()
        else:
            name, block = p[2]
            p[1][name] = block
            p[0] = p[1]

    def p_domain_block(self, p):
        '''domain_block : DOMAIN IDENT LCURLY req_section domain_list RCURLY'''
        d = Domain(name=p[2], requirements=p[4], domain_list=p[5])
        p[0] = ('domain', d)

    def p_req_section(self, p):
        '''req_section : REQUIREMENTS ASSIGN_EQUAL LCURLY string_list RCURLY SEMI
                       | REQUIREMENTS LCURLY string_list RCURLY SEMI
                       | empty'''
        if len(p) == 7:
            p[0] = p[4]
        elif len(p) == 6:
            p[0] = p[3]

    def p_domain_list(self, p):
        '''domain_list : domain_list type_section
                       | domain_list pvar_section
                       | empty'''
        if p[1] is None:
            p[0] = dict()
        else:
            name, section = p[2]
            p[1][name] = section
            p[0] = p[1]

    def p_type_section(self, p):
        '''type_section : TYPES LCURLY type_list RCURLY SEMI'''
        p[0] = ('types', p[3])

    def p_type_list(self, p):
        '''type_list : type_list type_def
                     | empty'''
        if p[1] is None:
            p[0] = []
        else:
            p[1].append(p[2])
            p[0] = p[1]

    def p_type_def(self, p):
        '''type_def : IDENT COLON OBJECT SEMI
                    | IDENT COLON LCURLY enum_list RCURLY SEMI'''
        if len(p) == 5:
            p[0] = (p[1], p[3])
        elif len(p) == 7:
            p[0] = (p[1], p[4])

    def p_enum_list(self, p):
        '''enum_list : enum_list COMMA ENUM_VAL
                     | ENUM_VAL
                     | empty'''
        if p[1] is None:
            p[0] = []
        elif len(p) == 4:
            p[1].append(p[3])
            p[0] = p[1]
        elif len(p) == 2:
            p[0] = [p[1]]

    def p_pvar_section(self, p):
        '''pvar_section : PVARIABLES LCURLY pvar_list RCURLY SEMI'''
        p[0] = ('pvariables', p[3])

    def p_pvar_list(self, p):
        '''pvar_list : pvar_list pvar_def
                     | empty'''
        if p[1] is None:
            p[0] = []
        else:
            p[1].append(p[2])
            p[0] = p[1]

    def p_pvar_def(self, p):
        '''pvar_def : nonfluent_def
                    | statefluent_def'''
        p[0] = p[1]

    def p_nonfluent_def(self, p):
        '''nonfluent_def : IDENT LPAREN param_list RPAREN COLON LCURLY NON_FLUENT COMMA type_spec COMMA DEFAULT ASSIGN_EQUAL range_const RCURLY SEMI
                         | IDENT COLON LCURLY NON_FLUENT COMMA type_spec COMMA DEFAULT ASSIGN_EQUAL range_const RCURLY SEMI'''
        if len(p) == 16:
            p[0] = NonFluent(name=p[1], range_type=p[9], param_types=p[3], def_value=p[13])
        else:
            p[0] = NonFluent(name=p[1], range_type=p[6], def_value=p[10])

    def p_statefluent_def(self, p):
        '''statefluent_def : IDENT LPAREN param_list RPAREN COLON LCURLY STATE COMMA type_spec COMMA DEFAULT ASSIGN_EQUAL range_const RCURLY SEMI
                           | IDENT COLON LCURLY STATE COMMA type_spec COMMA DEFAULT ASSIGN_EQUAL range_const RCURLY SEMI'''
        if len(p) == 16:
            p[0] = StateFluent(name=p[1], range_type=p[9], param_types=p[3], def_value=p[13])
        else:
            p[0] = StateFluent(name=p[1], range_type=p[6], def_value=p[10])

    def p_param_list(self, p):
        '''param_list : string_list'''
        p[0] = p[1]

    def p_type_spec(self, p):
        '''type_spec : IDENT
                     | INT
                     | REAL
                     | BOOL'''
        p[0] = p[1]

    def p_range_const(self, p):
        '''range_const : bool_type
                       | double_type
                       | int_type
                       | IDENT'''
        p[0] = p[1]

    def p_bool_type(self, p):
        '''bool_type : TRUE
                     | FALSE'''
        p[0] = True if p[1] == 'TRUE' else False

    def p_double_type(self, p):
        '''double_type : DOUBLE
                       | MINUS DOUBLE
                       | POS_INF
                       | NEG_INF'''
        p[0] = p[1] if len(p) == 2 else -p[2]

    def p_int_type(self, p):
        '''int_type : INTEGER
                    | MINUS INTEGER'''
        p[0] = p[1] if len(p) == 2 else -p[2]

    def p_instance_block(self, p):
        '''instance_block : INSTANCE IDENT LCURLY RCURLY'''
        i = Instance(p[2])
        p[0] = ('instance', i)

    def p_nonfluent_block(self, p):
        '''nonfluent_block : NON_FLUENTS IDENT LCURLY RCURLY'''
        nf = NonFluents(p[2])
        p[0] = ('non_fluents', nf)

    def p_string_list(self, p):
        '''string_list : string_list COMMA IDENT
                       | IDENT
                       | empty'''
        if p[1] is None:
            p[0] = []
        elif len(p) == 4:
            p[1].append(p[3])
            p[0] = p[1]
        elif len(p) == 2:
            p[0] = [p[1]]

    def p_empty(self, p):
        'empty :'
        pass

    def p_error(self, p):
        print('Syntax error in input!')

    def build(self, **kwargs):
        self._parser = yacc.yacc(module=self, **kwargs)

    def parse(self, input):
        return self._parser.parse(input=input, lexer=self.lexer)
