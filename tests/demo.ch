ps: Use 'ps' as one linear to write comments. We will use 'docstring' rather in this
ps: documentation. There is no ps ... sp style multiline stuff.

work `pd`(i)
    print(i -> |demo.md|)
    input("Press Enter to continue...")

`pd`(doc
# Welcome!

Welcome to chemistry helper, a complete calculator to bash your chemistry homework. It
does not have OOP, but it is a lot more powerful than a calculator -- it is Turing
complete. 

## Basic 4 Arithmetic

add:        1 + 2 + 3 + 4 = {1 + 2 + 3 + 4}
subtract:   20 - 1 = {20 - 1}
multiply:   1 * 2 * 3 = {1 * 2 * 3}
divide:     200 / 2 = {200 / 2}

## Advanced arithmetic

exponent:   2 ^ 3 = {2 ^ 3} or 2 ** 3 = {2 ** 3} (pythonic style)                                            
    > Exponent is right associtive. Consider
    2 ^ 3 ^ 4 == 2 ^ (3 ^ 4) = {2 ^ 3 ^ 4 == 2 ^ (3 ^ 4)}
    > Use bracket to allow expression of lower precedence to be evaluated
    2 ^ \{3 + 7\} = {2 ^ (3 + 7)}

modulo:     3 % 2 = {3 % 2}                                                    

## Unit awareness

unit aware: 10 mol NaCl + 20 mol NaCl = {10 mol NaCl + 20 mol NaCl}
    > There is no exception handling for the unit mismatch. Therefore if you put some weird
    unit, the calculator refuses to evaluate them rather than silently fail

    Try to execute: 10 mol NaCl + 20 mol NaOH. You will see the error message.

done)

`pd`(doc

## comparison

Eq:        1 == 1 = {1 == 1}
Neq:       1 != 1 = {1 != 1}
Lt:        1 < 2 = {1 < 2}
Le:        1 <= 2 = {1 <= 2}
Gt:        1 > 2 = {1 > 2}
Ge:        1 >= 2 = {1 >= 2}

    > Comparison is right associative also unit aware. You can't compare quantities with
    different units. Same as above, you will get an error message.

## Logical

And:        pass && fail = {pass && fail}
Or:         pass || fail = {pass || fail}
Not:        !pass = {!pass}

No XOR. If you want to, you have to use (a || b) && !(a && b)

done)

`pd`(doc

## Special literals

Path:       home\user\file.txt = {home\user\file.txt}
    > Path, without quote, is defined as any char except "<>/|?*()\{\}" and it must 
    not be a space
    > Path does not respect OS specific separator. It must always be \
    > Majority of time, lexical grammar of unquoted path fail. So use '|' to quote them
    like:
        |home\user\file.txt| = {home\user\file.txt}
    > I believe it is a design failure. But it is a trade off with OOP.

Quantity:   1 mol NaCl = {1 mol NaCl}
    > In this calculator, as a trade-off of speed, all the number is stored as
    (magnitude, unit, formula) 3 element tuple. All the magnitude is BCD(binary coded
    decimal), with default precision 28 (more specifications see python decimal) > There
    is no integer, float, or double => All are stored as Quantity, but formula-less and
    dimensionless.

Identifier: a
    > The problem with the identifier is -- it must not collide with the namespace of
    the unit (which is parsed by Pint), and must not collide with keywords or an
    infinite set of string, Formula. Later two are exactly described in EBNF grammar in
    README.
    > The lexer/scanner always treats alpha, number, and underscore sequence as
        - Element
        - Unit
        - Path
        - Identifier
    with priority from high to low, top to down. Hence, sometimes you must escape the
    identifier to use them, like
        - `NaCl` = 10 = {`NaCl` = 10}

Reaction:  :NaCl + H2O -> NaOH + H2:
    > Reaction is always preceding conversion operation, quoted by ':'.

done)

show_balanced_equation=fail

`pd`(doc
## Special features

Dimensional analysis made easy. Consider following problem, excerpt from our beloved
chemistry teacher, who we shall keep anonymous for the consideration of his/her
privacy:

    > How many moles of aqueous copper(II) sulfate would be required to precipitate all
    of the hydroxide ions present in a solution of sodium hydroxide containing 50.00
    grams of NaOH?

    Sol:
        - 50.00 g NaOH -> mol :CuSO4 + NaOH -> Cu(OH)2 + Na2SO4:-> CuSO4
    Ans:
        - {50.00 g NaOH -> mol :CuSO4 + NaOH -> Cu(OH)2 + Na2SO4:-> CuSO4}
    
    > How many grams of carbon dioxide can be produced by combusting 16.00 moles of
    butane (C4H10)?

    Sol:
        - 16.00 mol C4H10 :C4H10 + O2 -> CO2 + H2O:-> CO2 -> gram
    Ans:
        - {16.00 mol C4H10 :C4H10 + O2 -> CO2 + H2O:-> CO2 -> gram}

    > What mass of iron(II) carbonate can be produced by reacting 35.00 grams of
    potassium carbonate with an excess amount of iron(II) nitrate?
    
    Sol:
        - 35.00 g K2CO3 -> mol :K2CO3 + Fe(NO3)_{2} -> KNO3 + FeCO3:-> FeCO3 -> gram
    Ans:
        - {35.00 g K2CO3 -> mol :K2CO3 + Fe(NO3)_{2} -> KNO3 + FeCO3:-> FeCO3 -> gram}
    
If you want to show balanced equation, you can set environment variable
show_balanced_equation = pass. Vice versa, set it to fail to disable it. For your
reading experience, we disabled this feature in this document.
done)

`pd`(doc
## Programtic stuff

Yeah! Welcome to CS part of this calculator.

## Control flow

Exam is used to do something based on whether the exam is passed or failed. For example

gpa = 3.5
exam gpa > 3.5 
    print("A+") 
makeup gpa > 3.0 
    print("A") 
fail 
    print("F")

The above program gives a very cruel classification of GPA. 
    - Everyone who has GPA > 3.5 is A+
    - Everyone who has GPA > 3.0 is A
    - Everyone else is F

Redo and During are used to doing something repeatly. For example

i = 10
during i >= 0
    print(i)
    i -= 1

redo i of 1...11
    print(i)

Above two programs, will count from 10 to 0 and then back to 10.

For whatever reason, there is no exception handling. But I claim that is a feature
since if you failed the exam, you probably won't be able to try it again. (Really? Ok,
I admit it's just because iterating around the Python's implicit stack is hard.)
done)

`pd`(doc
## Abstraction

There is no OOP. All the calculation is do\ne by (home) Work. There is no default
argument, overloading, etc. But there is closure, first-order function (or function
pointer if you like), and recursion.

work move(n, from, buf, to)
    exam n == 1
        print(s"Move \{n\} from \{from\} to \{to\}")
    fail
        move(n - 1, from, to, buf)
        move(1, from, buf, to)
        move(n - 1, buf, from, to)
move(3, 'a', 'b', 'c')

Hanoi tower puzzle handler.

work fib(n)
    exam n <= 1
        submit 1
    fail
        res = fib(n-1) + fib(n-2)
        submit fib(n - 1) + fib(n - 2)

redo i of 1...20
    print(s'fib(\{i\}) = \{fib(i)\}')

Fibonacci sequence calculator.

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

A function that somehow remembers a nonlocal variable. 
done)

`pd`(doc

## IO

Just put -> after the expression, and the result will be collected. For example, you want
to print a multiply sheet with this language.

redo i of 1...10
    redo j of 1...10
        print(s'\{i\} x \{j\}
' -> |test.txt|)

And the result is collected in a file (more exactly, appended and created if not
exist), test.txt.

## Format String

This document is written with doc string. Read source code to find out how that works.
(Really, I don't put one here because I can't. This implementation takes advantage of
Python's find/KMP ago and always stop at the nearest stop point.)

You can use a bracket to quote expr, and then we will recursively evaluate expr and
fill its' stringify version to doc string. Doc string always supports that feature, but
you must prepend an s before normal string to enable that. done)

print(doc
## Bugs

This is probably one of the most exciting features of this calculator. Several things to
mention:
    - The parser is not perfect. If you feed it with invalid input, it will try to
    synchronize to the correct spot, which usually means, an infinite loop...
    - The scanner is quite weird. Since Pint allows you to use acronyms for the unit,
    one or two-character variable names usually get recognized as units.
    - The program is extremely slow, as it is an interpreter based on walking on AST.
    Similarly, we use an immutable environment, which means large memory copy overhead.
    And python is very slow too.
    - The calculator is not very stable (due to the dynamic typing nature of python).
    So we ask our beloved computer science teacher, whose name is also kept private for
    the consideration of his/her privacy, to give more practical suggestions about
        - How do share state across the entire project? Python does not support
        singleton, and you can't initialize the instance of the class as a static
        variable inside the class. You may initialize them as a global variable inside
        a module/file, but it would be re-initialized several times if the local import
        is used. In addition, global variables are generally not a good idea too.
            - How do you deal with circular import? We used the previous trick, init as
            a global object inside the file, but it does not work. Some objects, like
            an interpreter, which aims to be kept singleton, get initialized several
            times when we try to circumvent it with local import.
            - The current solution is hacking around __new__ and __init__ method plus some
            assertion
        - How do you handle exceptions in such a system? The current solution is using
        an error handler that prints the msg to stderr and returns an exception object
        for the callee to raise it. If it is fatal then raise/throw it. Otherwise, the
        program continues and ignores it. 
        - How to maintain a large project like that, without checking the type of every
        parameter? Currently, we use type hinting and MyPy, sometimes runtime
        isinstance as an assertion. But obviously, such kind of hack scattered over
        the entire project.
done)

`pd`(doc
        - Do you have any good ideas about overload? e.g., the handler claim that it will
        take a token or a line number or nothing to print to stderr. Python does not
        have overload, but the current solution is pretty much if isinstance, elif
        isinstance, else ...
        - And about keeping track of the evaluation process. Usually, we want to show
        the process of calculation, step by step. One way to do it, like we are
        currently implemented, is to hijack the interpreter and abstract syntax tree,
        force them to produce some sort of string in each step, and accumulate them
        (aka, syntax-directed translation). But this is not a good idea, since it
        essentially means mixing interpreters with a bunch of other stuff. Another way
        is decoupling it by creating some new class, that takes an interpreter to
        evaluate each node several time (e.g., you must have the molar mass of a
        compound, and only the interpreter know how to evaluate it). But the problem
        with that is it makes one pass operation to multiple passes. Or we hijack the
        objects themselves, but doing so forced them to manipulate a piece of
        list/tuple/etc. simultaneously, which introduces another piece of a global
        variable.

## Future

    - Add support for predicting chemical formula
    - Add support for better printing
    - Add support for GUI

## Thanks

    - For the inspiration for this calculator, thanks to my beloved chemistry teacher!
    - For the implementation of this calculator, thanks to my beloved CS teacher! 
    - And we will also thank Sympy for handling some heavy math stuff, Pint for unit
    parsing, the dragon book & crafting interpreters for the EBNF, CFG, predictive
    parser, recursive descent parser, and Python.

## License

    - MIT
done)