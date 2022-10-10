# Welcome!

Welcome to chemistry helper, a complete calculator to bash your chemistry
homework. It does not have OOP, but it is a lot more powerful than a
calculator — it is Turing complete. 

## Basic 4 Arithmetic

```
add:        1 + 2 + 3 + 4 = 10
subtract:   20 - 1 = 19
multiply:   1 * 2 * 3 = 6
divide:     200 / 2 = 100
```

## Advanced arithmetic

```
exponent:   2 ^ 3 = 8 or 2 ** 3 = 8 (pythonic style)        
```                                    
- Exponent is right associtive. Consider`2 ^ 3 ^ 4 == 2 ^ (3 ^ 4) = pass`
- Use bracket to allow expression of lower precedence to be evaluated `2 ^ {3 + 7} = 1024`

```
modulo:     3 % 2 = 1                                                    
```

## Unit awareness

```
unit aware: 10 mol NaCl + 20 mol NaCl = 30 mole NaCl
```

- There is no exception handling for the unit mismatch. Therefore if you put
  some weird unit, the calculator refuses to evaluate them rather than
  silently fail

Try to execute: `10 mol NaCl + 20 mol NaOH`. You will see the error message.

## Comparison

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

## Logical

```
And:        pass && fail = fail
Or:         pass || fail = pass
Not:        !pass = fail
```

No XOR. If you want to, you have to use `(a || b) && !(a && b)`

## Special literals

```
Path:       home\user\file.txt = home\user\file.txt
```

- Path, without quote, is defined as any char except "<>/|?*(){}" and it must 
  not contain a space
- Path does not respect OS specific separator. It must always be \
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

## Special features

Dimensional analysis made easy. Consider following problem, excerpt from our
beloved chemistry teacher:

> How many moles of aqueous copper(II) sulfate would be required to
> precipitate all of the hydroxide ions present in a solution of sodium
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

## Programtic stuff

Yeah! Welcome to CS part of this calculator.

## Control flow

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

## Abstraction

There is no OOP. All the calculation is do\ne by (home) Work. There is no
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

## IO


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

## Format String

This document is written with doc string. Read source code to find out how that works.

You can use a bracket to quote expr, and then we will recursively evaluate expr and
fill its' stringify version to doc string. Doc string always supports that feature, but
you must prepend an s before normal string to enable that.

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