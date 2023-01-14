from antlr4 import CommonTokenStream, InputStream, TerminalNode

from antlr2sitter import *

import argparse


class MyVisitor(ANTLRv4ParserVisitor):

    def visitParserRuleSpec(self, ctx: ANTLRv4Parser.ParserRuleSpecContext):
        name = str(ctx.RULE_REF())
        print(f"\t\t{name}: $ => ")
        if ctx.ruleBlock():
            print(ctx.ruleBlock().accept(self))
        print(",\n")

    def visitRuleBlock(self, ctx: ANTLRv4Parser.RuleBlockContext):
        return ctx.ruleAltList().accept(self)

    def visitRuleAltList(self, ctx: ANTLRv4Parser.RuleAltListContext):
        # return super().visitRuleAltList(ctx)
        if len(ctx.children) != 1:
            c = self.visit_list(ctx.labeledAlt())
            return "choice(" + ','.join(c) + ")"
        else:
            return ctx.labeledAlt(0).accept(self)

    def visitLabeledAlt(self, ctx: ANTLRv4Parser.LabeledAltContext):
        alt = ctx.alternative().accept(self)
        if ctx.identifier():
            return f"field('{ctx.identifier().accept(self)}', {alt})"
        return alt

    def visitIdentifier(self, ctx: ANTLRv4Parser.IdentifierContext):
        return str(ctx.RULE_REF() or ctx.TOKEN_REF() or ctx.ID())

    def visit_list(self, seq):
        return (x.accept(self) for x in seq)

    def visitBlock(self, ctx: ANTLRv4Parser.BlockContext):
        return ctx.altList().accept(self)

    def visitAlternative(self, ctx: ANTLRv4Parser.AlternativeContext):
        seq = list(filter(lambda x: x is not None, self.visit_list(ctx.element())))
        if len(seq) == 0:
            return "!!error!!"
        elif len(seq) == 1:
            return seq[0]
        elements = ', '.join(seq)
        return f"seq({elements})"

    def visitAltList(self, ctx:ANTLRv4Parser.AltListContext):
        if len(ctx.alternative())==1:
            return ctx.alternative(0).accept(self)
        seq = self.visit_list(ctx.alternative())
        j = ', '.join(seq)
        return f"choice({j})"


    def visitElement(self, ctx: ANTLRv4Parser.ElementContext):
        if ctx.actionBlock():
            return "!!action-block not supported!!"

        child = (ctx.labeledElement() or
                 ctx.atom() or
                 ctx.ebnf()).accept(self)

        sfx: ANTLRv4Parser.EbnfSuffixContext
        if sfx := ctx.ebnfSuffix():
            return self.ebnf_suffix(child, sfx)
        return child

    def ebnf_suffix(self, child: str, sfx: ANTLRv4Parser.EbnfSuffixContext) -> str:
        if sfx.STAR() is not None:
            return f"repeat({child})"
        if sfx.PLUS() is not None:
            return f"repeat1({child})"
        if sfx.QUESTION() is not None:
            return f"optional({child})"
        return child

    def visitLabeledElement(self, ctx: ANTLRv4Parser.LabeledElementContext):
        alt = (ctx.atom() or ctx.block()).accept(self)
        return f"field('{ctx.identifier().accept(self)}', {alt})"

    def visitAtom(self, ctx: ANTLRv4Parser.AtomContext):
        return super().visitAtom(ctx)

    def visitTerminal_(self, ctx: ANTLRv4Parser.Terminal_Context):
        if ctx.STRING_LITERAL() is not None:
            v = str(ctx.STRING_LITERAL()).strip('"')
            return f"{v}"
        else:
            return f"$.{ctx.TOKEN_REF()}"

    def visitRuleref(self, ctx: ANTLRv4Parser.RulerefContext):
        return f"$.{ctx.RULE_REF()}"

    def visitNotSet(self, ctx: ANTLRv4Parser.NotSetContext):
        return super().visitNotSet(ctx)

    def visitEbnf(self, ctx: ANTLRv4Parser.EbnfContext):
        c = ctx.block().accept(self)
        if ctx.blockSuffix():
            return self.ebnf_suffix(c, ctx.blockSuffix().ebnfSuffix())
        return c

    def visitLexerRuleSpec(self, ctx: ANTLRv4Parser.LexerRuleSpecContext):
        name = str(ctx.TOKEN_REF())
        print(f"\t\t{name}: $ => ", end="")
        print(ctx.lexerRuleBlock().accept(self), end="")
        print(",\n")

    def visitLexerAltList(self, ctx: ANTLRv4Parser.LexerAltListContext):
        if len(ctx.children) != 1:
            c = self.visit_list(ctx.lexerAlt())
            return '|'.join(c)
        else:
            return ctx.lexerAlt(0).accept(self)

    def visitLexerAlt(self, ctx: ANTLRv4Parser.LexerAltContext):
        return ctx.lexerElements().accept(self)

    def visitLexerElements(self, ctx: ANTLRv4Parser.LexerElementsContext):
        seq = list(filter(lambda x: x is not None, self.visit_list(ctx.lexerElement())))
        if len(seq) == 0:
            return "!!error!!"
        elif len(seq) == 1:
            return seq[0]
        elements = ''.join(seq)
        return f"{elements}"

    def visitLexerElement(self, ctx: ANTLRv4Parser.LexerElementContext):
        if ctx.actionBlock(): return "/*action-block*/";

        child = (ctx.lexerAtom() or ctx.lexerBlock()).accept(self)
        if sfx := ctx.ebnfSuffix():
            return child

        return child

    def visitLabeledLexerElement(self, ctx: ANTLRv4Parser.LabeledLexerElementContext):
        return super().visitLabeledLexerElement(ctx)

    def visitLexerBlock(self, ctx: ANTLRv4Parser.LexerBlockContext):
        return super().visitLexerBlock(ctx)

    def visitLexerAtom(self, ctx: ANTLRv4Parser.LexerAtomContext):
        if ctx.LEXER_CHAR_SET() or ctx.DOT():
            return ""
        return (ctx.characterRange() or ctx.terminal_() or ctx.notSet()).accept(self)

    def visitCharacterRange(self, ctx: ANTLRv4Parser.CharacterRangeContext):
        a = ctx.STRING_LITERAL(0)
        b = ctx.STRING_LITERAL(1)
        return f"[{a}-{b}]"


argparser = argparse.ArgumentParser()
argparser.add_argument("grammars", action="store", nargs='+')


def main():
    args = argparser.parse_args()

    print("{\n")
    print("\trules: {")

    for grammar in args.grammars:
        with open(grammar) as fp:
            lexer = ANTLRv4Lexer(InputStream(fp.read()))
        parser = ANTLRv4Parser(CommonTokenStream(lexer))
        ctx = parser.grammarSpec()
        ctx.accept(MyVisitor())

    print("\n\t}\n\n}\n")


if __name__ == "__main__": main()
