
import os
import inspect
import sqlite3
import time
from datetime import datetime


import contextlib as cl

debug_sql = os.getenv('DEBUGSQL')

class DatabaseError(sqlite3.DatabaseError):
    pass

class VarsTableError(DatabaseError):
    pass

class TableError(DatabaseError):
    pass

class TableExistsError(TableError):
    pass

class SQLDeclarationError(DatabaseError):
    pass

class AbstractSQLColumn(object):
    """An object holding the basic attributes for the ConcreteSQLColumn.

    These components of an SQLTable class are replaced with
    ConcreteSQLColumns in the SQLTable instances, with links to the
    SQLTable instance and requisite foreign SQLTable instances.
    """

    primary_key = False
    column_type=''
    
    declaration_count = 0

    def __init__(self, foreign_key=None, unique=False):
        self.declaration_order = AbstractSQLColumn.declaration_count
        AbstractSQLColumn.declaration_count += 1

        column_type = self.column_type
        self.column_type = column_type
        self.foreign_key = foreign_key

        self.unique = unique

        assert not self.primary_key 

    def sql_line(self, name):
        column_type = self.column_type
        return """%(name)s %(column_type)s""" % locals()

    def __str__(self):
        try:
            return "Abstract <%s> in '%s (%s) [%s]' [%s]" % (self.column_type, self.abstract_table.table_name, self.abstract_table.__name__, id(self.abstract_table), id(self))
        except AttributeError:
            return "Abstract <%s> in unknown table [%s]" % (self.column_type, id(self))

class Integer(AbstractSQLColumn):
    column_type='INTEGER'

class Real(AbstractSQLColumn):
    column_type='REAL'

class Text(AbstractSQLColumn):
    column_type='TEXT'

class Blob(AbstractSQLColumn):
    column_type='BLOB'


def type_name_to_class(type_name):
    if type_name == '':
        return AbstractSQLColumn

    type_name = type_name.upper()
    for cls in AbstractSQLColumn.__subclasses__():
        if cls.column_type.upper() == type_name:
            return cls
    raise Exception('No column class associated to "%s"' % type_name)



def find_foreign_key_table(foreign_key, foreign_tables):

    for table in foreign_tables:
        assert isinstance(table, SQLTable), "foreign_key_table is the wrong type: %s" % table
        for name, column in table.abstract_columns():
            if column is foreign_key:
                return table
        
    raise SQLDeclarationError("Foreign key '%s' not in '%s'" % (foreign_key, [[str(column.abstract_column_obj) for column in table.columns] for table in foreign_tables]))

def get_foreign_key_column(abstract_column_obj, foreign_table):
    if not abstract_column_obj.foreign_key:
        return None

    target_abstract_column_obj = abstract_column_obj.foreign_key

    for foreign_column_obj in foreign_table.columns:
        foreign_abstract_column_obj = foreign_column_obj.abstract_column_obj
        if foreign_abstract_column_obj is target_abstract_column_obj:
            return foreign_column_obj
    raise SQLDeclarationError("Abstract column obj '%s' not in foreign table '%s'" % (target__abstract_column_obj, foreign_table))


def check_valid_sql_expr_component(x):
    if not (isinstance(x, SQLExpr) or isinstance(x, ConcreteSQLColumn)):
        raise SQLDeclarationError('Unsupported SQLExpr component: %s' % x)
    return True

def convert_to_sql_type(x):
    if any(isinstance(x, t) for t in (str, unicode, int, float)):
        return x
    else:
        raise SQLDeclarationError("Unknown SQL type: %s (%s)" % (type(x), x))
        

def sql_expr(expr):
    """Create an SQLExpr from the argument."""
    if isinstance(expr, SQLExpr):
        return expr
    else:
        return SQLExpr("?", tuple(), (convert_to_sql_type(expr),))

class SQLExpr(object):
    
    def __init__(self, expr, columns, args):
        self.__expr = expr
        self.__columns = columns
        self.__args = args

    def __str__(self):
        if self.__args:
            return str(self.__args[0])
        else:
            return str(self.__expr)

    @property
    def args(self):
        return self.__args

    @property
    def expr(self):
        return self.__expr

    @property
    def columns(self):
        return self.__columns

    def __and__(self, other):
        return SQLAnd(self, other)

    def __or__(self, other):
        return SQLOr(self, other)

    def __invert__(self):
        return sql_not(self)


    def __lt__(self, other):
        return SQLLT(self, other)

    def __le__(self, other):
        return SQLLE(self, other)


    def __gt__(self, other):
        return SQLGT(self, other)

    def __ge__(self, other):
        return SQLGE(self, other)


    def __eq__(self, other):
        return SQLEq(self, other)

    def __ne__(self, other):
        return SQLNEq(self, other)


    def is_in(self, item):
        return SQLIn(self, item)

    def not_in(self, item):
        return SQLNotIn(self, item)


class SQLNot(SQLExpr):
    
    def __init__(self, expr):
        self.inner_expr = expr

    @property
    def expr(self):
        return 'NOT (%s)' % self.inner_expr.expr

    @property
    def columns(self):
        return self.inner_expr.columns

    @property
    def args(self):
        return self.inner_expr.args

    def __str__(self):
        return ' not (%s) ' % (self.inner_expr)


class SQLBinaryOp(SQLExpr):
    """Abstract base class of where logical op"""
    
    def __init__(self, left, right):
        self.left = sql_expr(left)
        self.right = sql_expr(right)

    @property
    def columns(self):
        return self.left.columns + self.right.columns

    @property
    def expr(self):
        return '%s %s (%s)' % (self.left.expr, self.op, self.right.expr)

    @property
    def args(self):
        return self.left.args + self.right.args

    def __str__(self):
        return ' (%s)%s(%s) ' % (self.left, self.op, self.right)




class SQLAnd(SQLBinaryOp):
    op = 'AND '

class SQLOr(SQLBinaryOp):
    op = 'OR '

class SQLLT(SQLBinaryOp):
    op = ' < '

class SQLLE(SQLBinaryOp):
    op = ' <= '


class SQLGT(SQLBinaryOp):
    op = ' > '

class SQLGE(SQLBinaryOp):
    op = ' >= '

class SQLEq(SQLBinaryOp):
    op = ' == '

class SQLNEq(SQLBinaryOp):
    op = ' != '


class SQLIn(SQLBinaryOp):
    op = ' IN '

class SQLNotIn(SQLBinaryOp):
    op = ' NOT IN '

def sql_not(x):
    if isinstance(x, SQLIn):
        return SQLNotIn(x.left, x.right)
    elif isinstance(x, SQLEq):
        return SQLNEq(x.left, x.right)
    elif isinstance(x, SQLNEq):
        return SQLEq(x.left, x.right)
    else:
        return SQLNot(sql_expr(x))


class ConcreteSQLColumn(SQLExpr):

    def __init__(self, table, name, abstract_column_obj, foreign_key_table=None, foreign_key_column=None):
        self.table = table
        assert is_valid_sql_name(name)
        self.__name = name.lower()
        self.abstract_column_obj = abstract_column_obj

        self.foreign_table = None
        if abstract_column_obj.foreign_key is not None:
            assert foreign_key_column is not None
            assert isinstance(foreign_key_table, SQLTable), "foreign_key_table is the wrong type: %s" % foreign_key_table
            assert abstract_column_obj.column_type == foreign_key_column.abstract_column_obj.column_type

            self.foreign_table = foreign_key_table
            self.foreign_key = foreign_key_column
        else:
            assert foreign_key_column is None
            self.foreign_key = None


    def is_join_key(self):
        return self.foreign_key and self.is_primary_key()

    @property
    def foreign_key_clause(self):
        foreign_key = self.foreign_key
        if foreign_key:
            foreign_column = foreign_key.unqualified_name
            foreign_table_name = self.foreign_table.table_name

            return " REFERENCES %(foreign_table_name)s (%(foreign_column)s) " % locals()
        else:
            return ""

    @property
    def unique(self):
        sql = ''
        if self.abstract_column_obj.unique:
            sql = ' UNIQUE '
        return sql

        
    def is_primary_key(self):
        return self.abstract_column_obj.primary_key

    @property
    def unqualified_name(self):
        return self.__name

    @property
    def qualified_name(self):
        return self.table.table_name + '.' + self.unqualified_name

    # SQLExpr overrides ####################
    @property
    def columns(self):
        return (self,)

    @property
    def args(self):
        return tuple()

    @property
    def expr(self):
        return self.qualified_name
    # SQLExpr overrides ^^^^^^^^^^^^^^^^^^^^

    def sql_line(self):
        return self.abstract_column_obj.sql_line(self.unqualified_name) + self.foreign_key_clause + self.unique

    def __str__(self):
        return self.qualified_name

    def __repr__(self):
        return '< ' + str(self) + ' >'


def primary_key(*columns):
    for column in columns:
        assert isinstance(column, AbstractSQLColumn)
        column.primary_key = True

class PrimaryKey(object):

    def __init__(self, *columns):
        self.columns = columns

class ConcretePrimaryKey(object):

    def __init__(self, *concrete_columns):
        assert all(isinstance(column, ConcreteSQLColumn) for column in concrete_columns)
        self.columns = tuple(concrete_columns)

    def sql_line(self):
        if self.columns != tuple():
            primary_key_columns = ', '.join(column.unqualified_name for column in self.columns)
            return 'PRIMARY KEY (%s)' % primary_key_columns
        else:
            return ''


class ForeignTableError(SQLDeclarationError):
    pass

        

class ForeignTable(object):
    """Object to encapsulate defining foreign key references for SQLTable declarations"""

    def __init__(self):
        self.required_columns = []

        
    def get_abstract_column(self, cls, name, **kwargs):
        self.required_columns.append((name, cls))

        return cls(foreign_key=(self, name), **kwargs)


    def Integer(self, name, **kwrgs):
        return self.get_abstract_column(Integer, name)


def is_primary_key(obj):
    return isinstance(obj, PrimaryKey)

def is_sql_column(obj):
    return isinstance(obj, AbstractSQLColumn)

def is_foreign_table(obj):
    return isinstance(obj, ForeignTable)


class SQLTableMetaClass(type):
    
    def __init__(cls, name, bases, dict):

        for member_name, member_obj in dict.iteritems():
            if isinstance(member_obj, AbstractSQLColumn):
                member_obj.abstract_table = cls
            elif isinstance(member_obj, ForeignTable):
                member_obj.name_in_declaration = member_name
        super(SQLTableMetaClass, cls).__init__(name, bases, dict)


class SQLTable(object):

    __metaclass__ = SQLTableMetaClass

    @property
    def table_name(self):
        try:
            return self.__table_name.lower()
        except AttributeError:
            return self.__class__.__name__.lower()

    @classmethod
    def abstract_columns(cls):
        columns  = list(inspect.getmembers(cls, is_sql_column))
        # sort the columns in the order they were declared.
        columns.sort(key=lambda c: c[1].declaration_order)        

        return columns

    @classmethod
    def foreign_tables(cls):
        return inspect.getmembers(cls, is_foreign_table)

    def __init__(self, **kwargs):
        # replace columns with concrete classes

        if 'name' in kwargs:
            self.__table_name = kwargs['name'].lower()

        table_name = self.table_name
        columns = []
        primary_keys = []
        table = self

        foreign_tables = {}
        for name_in_declaration, foreign_table in self.foreign_tables():
            if name_in_declaration not in kwargs:
                raise ForeignTableError("No table provided for foreign table '%s' when instantiating '%s'" % (name_in_declaration, table_name))
            foreign_table_instance = kwargs[name_in_declaration]

            for column_name, column_cls in foreign_table.required_columns:
                if not hasattr(foreign_table_instance, column_name):
                    raise ForeignTableError("Table provided for foreign table '%s' does not contain a column named '%s'" % (name_in_declaration, column_name))

                abstract_column = getattr(foreign_table_instance, column_name).abstract_column_obj
                if not isinstance(abstract_column, column_cls):
                    raise ForeignTableError("Foreign table column class is %s, not %s, as expected." % (type(abstract_column), column_cls))
            foreign_tables[name_in_declaration] = foreign_table_instance

        for column_name_in_declaration, abstract_column in self.abstract_columns():
            column_kwargs = {}
            if abstract_column.foreign_key:
                foreign_table, column_name = abstract_column.foreign_key
                foreign_table_instance = foreign_tables[foreign_table.name_in_declaration]

                column_kwargs['foreign_key_table'] = foreign_table_instance
                column_kwargs['foreign_key_column'] = getattr(foreign_table_instance, column_name)

            member_name = column_name_in_declaration
            name_option = member_name + '_name' 
            if name_option in kwargs:
                member_name = kwargs[name_option]

            concrete_column = ConcreteSQLColumn(table, member_name, abstract_column, **column_kwargs)
            setattr(self, member_name, concrete_column)
            columns.append(concrete_column)
            if concrete_column.is_primary_key():
                primary_keys.append(concrete_column)
        self.columns = columns

        if columns == []:
            raise SQLDeclarationError('No columns in table "%s"' % self.table_name)


        self.primary_key = ConcretePrimaryKey(*primary_keys)
            

    def sql_table(self):
        table_name = self.table_name

        sql_lines = []
        
        sql_lines.extend(column.sql_line() for column in self.columns)

        primary_key_sql_line = self.primary_key.sql_line()
        if primary_key_sql_line:
            sql_lines.append(primary_key_sql_line)

        sql_lines = ',\n'.join(sql_lines)

        return """CREATE TABLE IF NOT EXISTS %(table_name)s (
%(sql_lines)s
);""" % locals()

    def __str__(self):
        return self.sql_table() + '[%s]' % id(self)

    def __repr__(self):
        return '< ' + str(self) + ' >'
        
    def __eq__(self, other):
        if isinstance(other, SQLTable):
            my_sql = self.sql_table()
            other_sql = other.sql_table()

            return my_sql == other_sql
        else:
            return NotImplemented

    def __ne__(self, other):
        return not(self == other)

class SQLSyntaxError(Exception):
    pass


special_tokens = set([',', '.', '(', ')', ';'])

def is_valid_sql_name(name):
    valid = name[0].isalpha() and all(c.isalnum() or c=='_' for c in name)
    return valid


def __token_split(s):

    unprocessed_tokens = s.split()

    tokens = []

    while unprocessed_tokens != []:
        token = unprocessed_tokens.pop()

        if token == '':
            continue

        if len(token) == 1:
            assert is_valid_sql_name(token) or token in special_tokens
            tokens.append(token)
            continue

        # Split and keep as an individual token, any of the following
        # special characters.
        special_idx = -1
        for special in special_tokens:
            special_idx = token.find(special)
            if special_idx >= 0:
                break


        if special_idx >= 0:
            a, s, b = token[:special_idx], token[special_idx], token[special_idx+1:]
            unprocessed_tokens.extend([a, s, b])
        else:

            assert is_valid_sql_name(token)
            tokens.append(token)

    return tokens


    

def parse_table(sql_table, ref_tables=[]):

    if debug_sql=='ALL':
        print '\nParsing \n"""%s"""\n' % sql_table

    ref_tables = dict((table.table_name, table) for table in ref_tables)

    tokens = __token_split(sql_table)#sql_table.split()

    try:
        return __parse_table_tokens(tokens, ref_tables)
    except SQLSyntaxError as e:
        if debug_sql:
            print 'Syntax error parsing: ', sql_table
        raise 



def __parse_table_tokens(tokens, ref_tables):

    def parse_name():
        token = tokens.pop()
        if token in special_tokens:
            raise SQLSyntaxError('Expected valid variable name, got "%s"' % token)
        return str(token.lower())

    def expect_token(expected):
        token = tokens.pop().upper()

        if token != expected.upper():
            raise SQLSyntaxError("Encountered '%s' when expecting '%s'" % (token, expected))


    def expect_tokens(expecteds):
        for expected in expecteds:
            expect_token(expected)

    def acceptable_token(acceptable, leave=False):
        acceptable = [x.upper() for x in acceptable]

        token = tokens.pop()

        if token.upper() in acceptable:
            if leave:
                tokens.append(token)
            return token

        tokens.append(token)

        return False


    expect_token('CREATE')

    acceptable_token(['TEMP', 'TEMPORARY'])

    expect_token('TABLE')

    if acceptable_token(['IF']):
        expect_tokens(['NOT', 'EXISTS'])

    the_table_name = parse_name()

    # it's possible to see a '.' here

    expect_token('(')

    # class ParsedTable(SQLTable):
    #     table_name=the_table_name

    class ForeignKeyConstraint(object):

        def __init__(self, foreign_table_alias, foreign_table_name, foreign_column_name):
            self.foreign_table_alias = foreign_table_alias
            self.foreign_table_name = foreign_table_name
            self.foreign_column_name = foreign_column_name

    def parse_foreign_key_constraint():
        foreign_table_name = parse_name()
        assert foreign_table_name not in special_tokens

        alias = 'foreign_table_' + foreign_table_name

        expect_token('(') # I'm not sure how to handle NOT receiving the foreign column name
        foreign_column_name = tokens.pop()
        expect_token(')')
        
        return ForeignKeyConstraint(alias, foreign_table_name, foreign_column_name)

    def parse_column_constraint():
        constraint = acceptable_token(['UNIQUE', 'REFERENCES'])
        if not constraint:
            bad_constraint = tokens.pop()
            raise SQLSyntaxError("Unable to parse constraint: %s (%s)" % (bad_constraint, type(bad_constraint)))
        else:
            constraint = constraint.upper()

        if constraint == 'REFERENCES':
            return parse_foreign_key_constraint()
        elif constraint == 'UNIQUE':
            return 'UNIQUE'

        raise Exception("Unreachable line")


    def possible_type_token():
        token = acceptable_token(['INTEGER', 'REAL', 'TEXT', 'BLOB'])
        if not token:
            token = ''
        return token
        

    class ColumnDescription(object):
        def __init__(self, column_name, cls, foreign_key_constraint, column_kwargs):
            self.name = column_name
            self.cls = cls
            self.foreign_key_constraint = foreign_key_constraint
            self.column_kwargs = column_kwargs

    def parse_column():
        column_name = parse_name()

        foreign_key_constraint = None
        column_kwargs = []

        if acceptable_token([',', ')'], leave=True):
            ColumnClass = AbstractSQLColumn
        else:
            type_name = possible_type_token()
            ColumnClass = type_name_to_class(type_name)

            while not acceptable_token([',', ')'], leave=True):
                constraint = parse_column_constraint()
                if constraint == 'UNIQUE':
                    column_kwargs.append(('unique', True))
                elif isinstance(constraint, ForeignKeyConstraint):
                    foreign_key_constraint = constraint

            column_kwargs = dict(column_kwargs)

        return ColumnDescription(column_name, ColumnClass, foreign_key_constraint, column_kwargs)

    
    class TableConstraint(object):
        def __init__(self, constraint_type, column_names):
            self.constraint_type = constraint_type
            self.column_names = column_names

        def apply(self, clsdict):
            assert self.constraint_type == 'PRIMARY'
            primary_key(*[clsdict[column_name] for column_name in self.column_names])


    def parse_table_constraint():

        # def parse_primary_column():
        #     indexed_column_name = parse_name()
            

        constraint_type = parse_name().upper()
        
        if constraint_type == 'PRIMARY':
            
            expect_token('KEY')
            expect_token('(')

            primary_column_names = [parse_name()]
            while acceptable_token([',']):
                primary_column_names.append(parse_name())

            expect_token(')')
        else:
            raise SQLSyntaxError('Not able to handle table constraint "%s"' % constraint_type)

        return TableConstraint(constraint_type, primary_column_names)

    columns = []
    table_constraints = []
            
    # There must be a first column
    columns.append(parse_column())

    while acceptable_token([',']):
        if acceptable_token(['PRIMARY'], leave=True):
            table_constraints.append(parse_table_constraint())
            break
        else:
            columns.append(parse_column())

    expect_token(')')


    clsdict = {'table_name': the_table_name}

    required_tables = []

    for column_description in columns:
        cls = column_description.cls
        if column_description.foreign_key_constraint:
            constraint = column_description.foreign_key_constraint
            alias = constraint.foreign_table_alias
            
            if alias in clsdict:
                foreign_table = clsdict[alias]
            else:
                clsdict[alias] = foreign_table = ForeignTable()

            abstract_column = foreign_table.get_abstract_column(cls, constraint.foreign_column_name, **column_description.column_kwargs)

            try:
                ref_table = ref_tables[constraint.foreign_table_name]
            except KeyError:
                raise SQLSyntaxError('Reference table "%s" is not provided in ref_tables.' % (constraint.foreign_table_name))

            required_tables.append((alias, ref_table))
        else:
            abstract_column = cls(**column_description.column_kwargs)

        clsdict[column_description.name] = abstract_column

    for constraint in table_constraints:
        constraint.apply(clsdict)
    
    ParsedTableClass = SQLTableMetaClass(the_table_name, (SQLTable,), clsdict)
    
    
    return ParsedTableClass(**dict(required_tables))


    

def join_key(table_i, table_j):
    """Returns the column to join on if True if table_i has a foreign_key reference to table_j"""

    j_keys = [column for column in table_j.columns if column.foreign_key or column.is_primary_key()]
    j_foreign_keys = dict((column.foreign_key, column) for column in table_j.columns if column.foreign_key)


    for column in table_i.columns:
        foreign_key = column.foreign_key
        if foreign_key:
            for key in j_keys:
                if foreign_key is key or (key.foreign_key and foreign_key is key.foreign_key):
                    return column, key
        elif column.is_primary_key():
            for key in j_keys:
                if column is key.foreign_key:
                    return column, key
    return None

def find_join_key(table, joinable_tables):
    for joinable_table in joinable_tables:
        join_pair = join_key(table, joinable_table)
        if join_pair:
            return join_pair
    return None

def join_pairs(tables):

    joined_tables, unjoined_tables = tables[:1], tables[1:]

    join_pairs = []

    while unjoined_tables != []:
        for unjoined_table in unjoined_tables:
            join_pair = find_join_key(unjoined_table, joined_tables)
            if join_pair:
                break

        if not join_pair:
            print joined_tables
            print unjoined_tables
            raise Exception("Unable to join tables: %s\n split on %s %s" % ([table.table_name for table in tables], 
                                                                            [table.table_name for table in joined_tables],
                                                                            [table.table_name for table in unjoined_tables]))
        
        unjoined_tables.remove(unjoined_table)
        joined_tables.append(unjoined_table)
        join_pairs.append(join_pair)

    return join_pairs
        

def select(columns, where=None):
    all_columns = columns[:]
    if where:
        all_columns.extend(where.columns)

    tables = list(set([column.table for column in all_columns]))

    # joinable_keys = set()

    # for table in tables:
    #     joinable_keys.update(column for column in table.columns if (column.is_primary_key() or column.foreign_key) )

    # tables.sort(key=lambda t: sum(1 for c in t.columns if c.foreign_key in joinable_keys and  c.foreign_key in joinable_keys))

    result_columns = ', '.join(column.qualified_name for column in columns)

    # Find a common foreign key, and inner join on that

    # for each table, inner join on all the common foreign keys in
    # the foreign key set, and then add *all* foreign keys to the
    # foreign key set.
    join_source = tables[0].table_name

    for join_pair in join_pairs(tables):
        new_table = join_pair[0].table.table_name
        left_column = join_pair[0].qualified_name
        right_column = join_pair[1].qualified_name

        join_source += ' INNER JOIN %(new_table)s ON %(left_column)s=%(right_column)s ' % locals()

    # join_source = ', '.join(table.table_name for table in tables)

    expr = ''
    args = tuple()
    if where:
        expr = ' WHERE %s' % where.expr
        args = where.args

    sql = 'SELECT %(result_columns)s FROM %(join_source)s%(expr)s' % locals()

    return SQLExpr(sql, tuple(), args)

class Vars(SQLTable):
    name = Text(unique=True)
    value = Text()


class DatabaseMixin(object):

    __tables = None

    @property
    def tables(self):
        if self.__tables is not None:
            return self.__tables

        self.__tables = []
        return self.__tables

    def __open_sql_db(self, dbname, create):
        self.dbname = dbname

        if create is not None:
            exists = os.path.exists(dbname)
            if create:
                if exists:
                    os.remove(dbname)
            else:
                if not exists:
                    raise DatabaseError("Database does not exist: %s" % dbname)
        create = not os.path.exists(dbname)

        self.sql_db = sqlite3.connect(dbname)

        return create

    def __create_tables(self, tables):
        sql = ';\n'.join(table.sql_table() for table in tables)
        self.executescript(sql)
        self.tables.extend(tables)

    def __drop_table(self, table_name):
        sql = 'DROP TABLE IF EXISTS %s'% table_name
        self.executescript(sql)

    @property
    def __master_table_names(self):

        for name, in self.execute("SELECT name FROM sqlite_master"):
            yield name

    @property
    def __master_sql_table(self):
        for sql, in self.execute("SELECT sql FROM sqlite_master"):
            if sql:
                yield sql

    def _add_table(self, table):
        assert isinstance(table, SQLTable)
        table_name = table.table_name.lower()
        assert any(name.lower() == table_name for name in self.__master_table_names), "tried to _add_table a table not in the sql database."

        self.__tables.append(table)

        setattr(self, table.table_name.lower(), table)

        return table

    def _remove_table(self, table):
        assert isinstance(table, SQLTable)
        table_name = table.table_name.lower()

        assert any(name.lower() == table_name for name in self.__master_table_names), "tried to _remove_table '%s' which is not in the database." % table.table_name
        assert getattr(self, table_name.lower()) is table
        delattr(self, table_name.lower())
        self.__tables = [atable for atable in self.__tables 
                         if not table.table_name.lower() == atable.table_name.lower()]

    def __init__(self, dbname, *args, **kwargs):

        if 'create' in kwargs:
            create = kwargs['create']
        else:
            create = None

        create = self.__open_sql_db(dbname, create)

        for sql in self.__master_sql_table:
            new_table = self._add_table(parse_table(sql, ref_tables=self.tables))

        if create:
            with self.session():
                self.create_tables(*args, **kwargs)

        self.__last_checkpoint = time.time()

    def has_table(self, table_name):
        table_name = table_name.lower()
        for table in self.tables:
            if table.table_name == table_name:
                return table
        return False

    def get_table(self, table_name):
        table = self.has_table(table_name)
        if not table:
            raise TableError("No such table: '%s'" % table_name)
        return table


    def new_table(self, table, overwrite=False):
        assert isinstance(table, SQLTable)
        old_table = self.has_table(table.table_name)

        if old_table:
            if overwrite:
                self.drop_table(old_table.table_name)
            else:
                raise TableExistsError("Table '%s' already exists: %s" % (table.table_name, old_table))
        else:
            self.tables.append(table)

        self.__create_tables([table])

        self._add_table(table)

        return table

    def drop_table(self, table_name):
        table = self.has_table(table_name)
        if table:
            self._remove_table(table)

        self.__drop_table(table.table_name)


    def create_tables(self, *args, **kwargs):
        self.new_table(Vars())

    def checkpoint(self, check_time=5*60.):
        current_checkpoint = time.time()
        delta = current_checkpoint - self.__last_checkpoint
        if delta > check_time:
            self.sql_db.commit()
            self.__last_checkpoint = current_checkpoint

    @cl.contextmanager
    def session(self):
        try:
            yield

            if self.sql_db.total_changes > 0:
                self.set_modification_time()

            self.sql_db.commit()
        except:
            self.sql_db.rollback()
            raise

    def close(self):
        self.sql_db.close()

    @cl.contextmanager
    def cursor(self):
        c = self.sql_db.cursor()
        try:
            yield c
        finally:
            c.close()

    def execute(self, sql, args=tuple()):
        global debug_sql
        with self.cursor() as c:
            if debug_sql=='ALL':
                print sql, args
            try:
                for x in c.execute(sql, args):
                    yield x
            except:
                if debug_sql:
                    print 'Exception when executing "%s" with args "%s"' % (sql, args)
                raise
            if c.lastrowid is not None:
                yield c.lastrowid


    def executemany(self, sql, args=tuple(), checkpoint=False):
        global debug_sql

        if checkpoint:
            def checkpointed_args(args):
                for arg in args:
                    self.checkpoint()
                    yield arg
            args = checkpointed_args(args)

        with self.cursor() as c:
            if debug_sql=='ALL':
                print sql, args
            try:
                c.executemany(sql, args)
            except:
                if debug_sql:
                    print 'Exception when executing many "%s" with args "%s"' % (sql, args)
                raise



    def executescript(self, sql):
        global debug_sql
        with self.cursor() as c:
            if debug_sql=='ALL':
                print sql
            try:
                c.executescript(sql)
            except:
                if debug_sql:
                    print 'Exception when executing script "%s"' % (sql)
                raise


    def insert(self, table, values=[], checkpoint=False):

        table_name = table.table_name
        column_objs = table.columns
        columns = 'DEFAULT'
        qs = ''
        num_columns = len(column_objs)
        if (num_columns > 1) or (num_columns > 0 and values != []):
            columns = '(%s)' % (', '.join(column_obj.unqualified_name for column_obj in column_objs))
            qs = ' (%s)' % (', '.join('?' for column_obj in column_objs))            

        sql = "INSERT OR REPLACE INTO %(table_name)s %(columns)s VALUES%(qs)s" % locals()

        if values == []:
            for lastrowid in self.execute(sql):
                return lastrowid
        else:
            self.executemany(sql, values, checkpoint=checkpoint)

    def select(self, columns, where=None):

        select_expr = select(columns, where)

        sql, args = select_expr.expr, select_expr.args

        for row in self.execute(sql, args):
            yield row


    # TODO: create column modifiers so that sql functions of columns like MAX can be selected via regular db.select
    def select_max(self, column):
        column_name = column.unqualified_name
        table_name = column.table.table_name

        sql = 'SELECT MAX(%(column_name)s) FROM %(table_name)s' % locals()
        for row in self.execute(sql):
            return row[0]


    def select_min(self, column):
        column_name = column.unqualified_name
        table_name = column.table.table_name

        sql = 'SELECT MIN(%(column_name)s) FROM %(table_name)s' % locals()
        for row in self.execute(sql):
            return row[0]


    def select_min_max(self, column):
        column_name = column.unqualified_name
        table_name = column.table.table_name

        sql = 'SELECT MIN(%(column_name)s), MAX(%(column_name)s) FROM %(table_name)s' % locals()
        for row in self.execute(sql):
            return row


    def set_var(self, name, value):
        self.insert(self.vars, [(name, value)])

    def get_var(self, name):
        results = list(self.select([self.vars.value], where=(self.vars.name==name)))
        if len(results) > 1:
            print 'WARNING: len(results) > 1'
        if results == []:
            return None
        return results[-1][0]

    def ensure_var(self, name, default_value):
        assert isinstance(default_value, str)
        
        old_val = self.get_var(name)
        if old_val is None:
            self.set_var(name, default_value)
        else:
            if str(old_val) != str(default_value):
                raise VarsTableError('Old value of "%s" not equal to expected value: "%s" != "%s"' % (name, old_val, default_value))


    def set_modification_time(self):
        mod_time = datetime.now().strftime('%I:%M%p %d %B %Y')
        self.set_var('modified', mod_time)

    def get_modification_time(self):
        return self.get_var('modified')
