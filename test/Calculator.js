obj = {
    rules: {
        POW: $ => '^',
        MUL: $ => '*',
        DIV: $ => '/',
        ADD: $ => '+',
        SUB: $ => '-',
        NUMBER: $ => '',
        WHITESPACE: $ => null,
        start: $ => $.expression,
        expression: $ => choice(
            field('Number', $.NUMBER),
            field('Parentheses',
                seq('(', field('inner', $.expression), ')')),
            field('Power', seq(field('left', $.expression),
                field('operator', $.POW), field('right', $.expression))),
            field('MultiplicationOrDivision', seq(field('left', $.expression),
                field('operator', None), field('right', $.expression))),
            field('AdditionOrSubtraction', seq(field('left', $.expression),
                field('operator', None), field('right', $.expression))))
        ,
    }
}
