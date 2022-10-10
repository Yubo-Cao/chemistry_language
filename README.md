# Chemistry Utils

Welcome to chemistry helper, a complete calculator to bash your chemistry
homework. It does not have OOP, but it is a lot more powerful than a
calculator — it is Turing complete.

## Syntax

### Lexical grammar

```text
STR         -> ( "s" )? "\"" (not "\"" or "\"" with preceding "\\")* "\"" | ( "s" )? "doc" (any string sequence not including "done")+ "done"
FORMULA     -> compound ( "^" "{" NUMBER ( "+" | "-" ) "}" )? | compound ( "^" NUMBER ( "+" | "-" ) )?;
compound    -> ( ( ELEMENT | "(" ELEMENT ")" ) ( "_" "{" (any char that is not "}") "}" | "_" NUMBER | NUMBER )? )+;
PATH        ->  (path_car)* ( "\" (path_char " ")* )+ | "|" ( any char that is not "|" ) ( "\" ( any char that is not "|" )* )+ "|";
path_char   -> any char that is not "<>/|?*(){}" and not space
UNIT        -> "m" | "in" | "ft" | "yd" | "mi" | "acre" | "L" ... See pint default units.;
PLURAL      -> "s" | "es" | "ves" | "ies";
NUMBER      -> DIGIT+ ( "." DIGIT+ )? ( ( "e" | "E" ) DIGIT )?;
IDENTIFIER  -> ALPHA ( ALPHA | DIGIT )*;
ALPHA       -> "_" | "a" ... "z" | "A" ... "Z" | U+0000 ... U+10FFFF;
DIGIT       -> "0" ... "9";
ELEMENT     -> "H"|"He"|"Li"|"Be"|"B"|"C"|"N"|"O"|"F"|"Ne"|"Na"|"Mg"|"Al"|"Si"|"P"|"S"|"Cl"|"Ar"|"K"|"Ca"|"Sc"|"Ti"|"V"|"Cr"|"Mn"|"Fe"|"Co"|"Ni"|"Cu"|"Zn"|"Ga"|"Ge"|"As"|"Se"|"Br"|"Kr"|"Rb"|"Sr"|"Y"|"Zr"|"Nb"|"Mo"|"Tc"|"Ru"|"Rh"|"Pd"|"Ag"|"Cd"|"In"|"Sn"|"Sb"|"Te"|"I"|"Xe"|"Cs"|"Ba"|"La"|"Ce"|"Pr"|"Nd"|"Pm"|"Sm"|"Eu"|"Gd"|"Tb"|"Dy"|"Ho"|"Er"|"Tm"|"Yb"|"Lu"|"Hf"|"Ta"|"W"|"Re"|"Os"|"Ir"|"Pt"|"Au"|"Hg"|"Tl"|"Pb"|"Bi"|"Po"|"At"|"Rn"|"Fr"|"Ra"|"Ac"|"Th"|"Pa"|"U"|"Np"|"Pu"|"Am"|"Cm"|"Bk"|"Cf"|"Es"|"Fm"|"Md"|"No"|"Lr"|"Rf"|"Db"|"Sg"|"Bh"|"Hs"|"Mt"|"Ds"|"Rg"|"Cn"|"Nh"|"Fl"|"Mc"|"Lv"|"Ts"|"Og";
```

### Expression

```text
expr        -> interval;
write       -> interval -> PATH;
interval    -> assign "..." assign;
assign      -> identifier '=' expr;
ternary     -> "(" expr ")" "?" expr ":" expr 
or          -> and ( "|" and )*;
and         -> eq ( "&" eq )*;
eq          -> cp ( ("!=" | "==") cp )*;
cp          -> term ( ( ">" | ">=" | "<" | "<=" ) term)*;
term        -> factor ( ( "-" | "+" ) factor )*;
factor      -> unary ( ( "/" | "*" | "%" ) unary | ( reactions )?  ( "->"  ( UNIT | formula ) ) )*;
unary       -> ("!" | "-" | "+" | "~" ) unary | exp;
exp         -> call ( "**" | "^" ) "{" expr "}" | call ( "**" | "^" ) ( call );
call        -> primary ( "(" content? ")" ) | "." IDENTIFIER )*;
primary     -> IDENTIFIER | "pass" | "fail" | "(" expr ")" | "na" | STR | PATH | quantity;

identifier  -> IDENTIFIER | "`" IDENTIFIER "`"
reactions   -> ":" reaction ( "," reaction )* ":"
reaction    -> FORMULA  ( "+"  formula )* "->"  FORMULA ( "+" formula )*
quantity    -> primary ( unit )? ( formula )?;
content     -> expr ( "," expr )*;
unit        -> unit ( "/" | "*" ) UNIT ( "^" )? NUMBER  PLURAL? | UNIT PLURAL?;
```

### Statement

It is weird to call them statements. Since this is a super-cow-power
calculator, all the statements are evaluated and have a return value. But we
got to stop the evaluation of expression somewhere, so statements are still
preserved.

All the statements, if not followed by a newline, can be written as oneliner.
We allow you to write assignment expressions inside this oneliner, and it
will declare/define variables in a separate lexica scope of the statement.

For work, the last line of statements will be automatically submitted (Nobody
can write homework but forgot to submit!), if you do not explicitly put a
submit statement.

```text
stmt        ->  exam | redo | during | work | submit;
exam        -> "exam" expr SEP block ( "makeup" expr ( SEP block | expr ) )* ( "fail" SEP block )? SEP | "exam" expr ( "makeup" expr expr )* ( "fail" expr )?; 
redo        -> "redo" IDENTIFIER "of" interval ( SEP block | expr ) SEP;
during      -> "during" expr ( SEP block | expr ) SEP;
work        -> "work" IDENTIFIER "(" parameters? ")" ( SEP block | expr ) SEP;
submit      -> "submit" expr SEP;

parameters  -> IDENTIFIER ( "," IDENTIFIER )*;
block       -> INDENT stmt* DEDENT;

SEP         -> \n;
INDENT      -> ( "\t" | " " )*;
```

### Specification

- In this implementation, the recursive descent parser shall parse any expression that can
  be generated from the first production `expression -> interval`.
- A number without a unit is considered a scalar, which would only change the
  quantity in the expression (if any), but not their unit. However, if multiple units
  are found, dimensional analysis is running with `Graph`.
- Chemical formulas are treated as a `quantity` with `g/mol` as the unit. However, one could
  use a different aspect of the chemical formula to calculate, e.g., the sum of
  electronegativity, the sum of atomic numbers, etc.

## Execution

- This is an interpreter that evaluates/generate result through iteration of the tree,
  a.k.a., syntax-directed generation.

## Demo

### Basic 4 Arithmetic

```
add:        1 + 2 + 3 + 4 = 10
subtract:   20 - 1 = 19
multiply:   1 * 2 * 3 = 6
divide:     200 / 2 = 100
```

### Advanced arithmetic

```
exponent:   2 ^ 3 = 8 or 2 ** 3 = 8 (pythonic style)        
```

- Exponent is right associtive. Consider`2 ^ 3 ^ 4 == 2 ^ (3 ^ 4) = pass`
- Use bracket to allow expression of lower precedence to be evaluated `2 ^ {3 + 7} = 1024`

```
modulo:     3 % 2 = 1                                                    
```

### Unit awareness

```
unit aware: 10 mol NaCl + 20 mol NaCl = 30 mole NaCl
```

- There is no exception handling for the unit mismatch. Therefore if you put
  some weird unit, the calculator refuses to evaluate them rather than
  silently fail

Try to execute: `10 mol NaCl + 20 mol NaOH`. You will see the error message.

### Comparison

```
Eq:        1 == 1 = pass
Neq:       1 != 1 = fail
Lt:        1 < 2 = pass
Le:        1 <= 2 = pass
Gt:        1 > 2 = fail
Ge:        1 >= 2 = fail
```

- Comparison is right associative also unit aware. You can't compare
  quantities with different units (unless convertable). Same as above, you
  will get an error message.

### Logical

```
And:        pass && fail = fail
Or:         pass || fail = pass
Not:        !pass = fail
```

No XOR. If you want to, you have to use `(a || b) && !(a && b)`

### Special literals

```
Path:       home\user\file.txt = home\user\file.txt
```

- Path, without quote, is defined as any char except "\<>/|?\*(){}" and it must
  not contain a space
- Path does not respect OS specific separator. It must always be \\
- Majority of time, lexical grammar of unquoted path fail. So use '|' to
  quote them, like:

```
|home\user\file.txt| = home\user\file.txt
```

```
Quantity:   1 mol NaCl = 1 mole NaCl
```

- In this calculator, as a trade-off of speed, all the number is stored as
  (magnitude, unit, formula) 3 element tuple. All the magnitude is BCD(binary
  coded decimal), with default precision 28 (more specifications see python
  decimal)
- There is no integer, float, or double. All are stored as Quantity, but
  formula-less and dimensionless.

```
Identifier: a
```

- The problem with the identifier is -- it must not collide with the
  namespace of the unit (which is parsed by Pint), and must not collide
  with keywords or an infinite set of string, Formula. Later two are
  exactly described in EBNF grammar in README.

- The lexer/scanner always treats alpha, number, and underscore sequence as

  - Element
  - Unit
  - Path
  - Identifier

  with priority from high to low, top to down. Hence, sometimes you must
  escape the identifier to use them, like - \`NaCl\` = 10 = 10

```
Reaction:  :NaCl + H2O -> NaOH + H2:
```

- Reaction is always preceding conversion operation, quoted by ':'.

### Special features

Dimensional analysis made easy. Consider following problem, excerpt from our
beloved chemistry teacher:

> How many moles of aqueous copper(II) sulfate would be required to
> precipitate all the hydroxide ions present in a solution of sodium
> hydroxide containing 50.00 grams of NaOH?

```
Sol:
    - 50.00 g NaOH -> mol :CuSO4 + NaOH -> Cu(OH)2 + Na2SO4:-> CuSO4
Ans:
    - 0.6250625062506250799124776075 mole CuSO_{4}
```

> How many grams of carbon dioxide can be produced by combusting 16.00 moles
> of butane (C4H10)?

```
Sol:
    - 16.00 mol C4H10 :C4H10 + O2 -> CO2 + H2O:-> CO2 -> gram
Ans:
    - 2816.576000000000021827872843 gram CO_{2}
```

> What mass of iron(II) carbonate can be produced by reacting 35.00 grams of
> potassium carbonate with an excess amount of iron(II) nitrate?

```
Sol:
    - 35.00 g K2CO3 -> mol :K2CO3 + Fe(NO3)_2 -> KNO3 + FeCO3:-> FeCO3 -> gram
Ans:
    29.33963561112558265547152519 gram FeCO_{3}
```

If you want to show balanced equation, you can set environment variable
show_balanced_equation = pass. Vice versa, set it to fail to disable it. For your
reading experience, we disabled this feature in this document.

### Programtic stuff

Yeah! Welcome to CS part of this calculator.

### Control flow

Exam is used to do something based on whether the exam is passed or failed. For example

```
gpa = 3.5
exam gpa > 3.5 
    print("A+") 
makeup gpa > 3.0 
    print("A") 
fail 
    print("F")
```

The above program gives a very cruel classification of GPA.

- Everyone who has GPA > 3.5 is A+
- Everyone who has GPA > 3.0 is A
- Everyone else is F

`redo` and `during` are used to doing something repeatly. For example

```
i = 10
during i >= 0
    print(i)
    i -= 1

redo i of 1...11
    print(i)
```

Above two programs, will count from 10 to 0 and then back to 10.

### Abstraction

There is no OOP. All the calculation is done by (home) Work. There is no
default argument, overloading, etc. But there is closure, first-order
function (or function pointer if you like), and recursion.

- Hanoi tower puzzle handler.

  ```
  work move(n, from, buf, to)
      exam n == 1
          print(s"Move {n} from {from} to {to}")
      fail
          move(n - 1, from, to, buf)
          move(1, from, buf, to)
          move(n - 1, buf, from, to)
  move(3, 'a', 'b', 'c')
  ```

- Fibonacci sequence calculator.

  ```
  work fib(n)
      exam n <= 1
          submit 1
      fail
          res = fib(n-1) + fib(n-2)
          submit fib(n - 1) + fib(n - 2)

  redo i of 1...20
      print(s'fib({i}) = {fib(i)}')
  ```

A function that remembers a nonlocal variable, through usage of closure.
Notice in this implementation of closure, there is no `__closure__` variable
to access the nonlocal variable. Instead, it is some magic that is hidden.

```
work counter()
    i = 0
    work impl()
        print(i)
        i += 1
    submit impl

i = counter()
i()
i()
i()
```

### IO

Just put `->` after the expression, and the result will be collected. For
example, you want to print a multiply sheet with this language.

```
redo i of 1...10
    redo j of 1...10
        print(s'{i} x {j}
' -> |test.txt|)
```

And the result is collected in a file (more exactly, appended and created if not
exist), `test.txt`.

### Format String

This document is written with doc string. Read source code to find out how that works.

You can use a bracket to quote expr, and then we will recursively evaluate expr and
fill its' stringify version to doc string. Doc string always supports that feature, but
you must prepend an s before normal string to enable that.

### Future

- Add support for predicting chemical formula
- Add support for better printing
- Add support for GUI

### Thanks

- For the inspiration for this calculator, thanks to my beloved chemistry teacher!
- For the implementation of this calculator, thanks to my beloved CS teacher!
- And we will also thank Sympy for handling some heavy math stuff, Pint for unit
  parsing, the dragon book & crafting interpreters for the EBNF, CFG, predictive
  parser, recursive descent parser, and Python.

## License

- MIT
