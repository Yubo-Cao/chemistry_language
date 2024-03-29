I want to tell you about Chemistry Language, a language design to help chemistry instructors and students to solve chemistry problems.

This language takes care of significant digits while supporting common operations in all languages. For example, it supports addition, subtraction, multiplication, division, modulo, and exponentiation. Exponentiation is also supported in both pascal and python style.

```ch
print(1.2345 + 1.2)     ps: adding takes least decimal places
print(1.9 - 2.0)
print(2.0 * 3.24)       ps: multiplying takes least sig figs
print(2.0 / 3.0)
print(2.0 % 3.0)
print(2.0 ^ 3)          ps: exponents are like repeated multiplication
print(2.0 ^ 3 ** 3)     ps: supports pascal and python style exponentiation
print(2.0 ** 3 ** 3 == 2.0 ** (3 ** 3))
```

It also has a few built-in functions. Notice that significant digits is preserved throughout the operation.

```ch
print(log(100))         ps: log base 2 by default
print(log10(100))       ps: log base 10
print(sin(10))          ps: -0.5
print(cos(10.0))        ps: -0.839
```

The most important feature of this langauge is that it can handle dimensional analysis. It also comes with automatic
unit conversion.

```ch
print(10 mol NaCl + 20 mol NaCl)    ps: 3×10¹ mol NaCl
print(10 kmol NaCl + 20 mol NaCl)   ps: 1×10¹ kmol NaCl
print(10.000 km + 20.000 m)         ps: 10.020 km
print(10.000 km + 20.000 m -> mm)   ps: 1.0020×10⁷ mm
```

It also prevents you from making mistakes. For example, adding kilometer to gram is not allowed, and neither as mixing two substances that's not the same:

```ch
print(10.00 km + 20.00 g NaCl)      ps: error: can't convert gram to kilometer
print(10.00 g H2O + 20.00 g NaCl)   ps: error: cannot convert H₂O to NaCl
```

However, it's also smart enough to know what you want to do. For example, it automatically
calculates the number of moles of water in a solution and guess the desired unit based on
order of operands:

```ch
print(10.00 g H2O + 1.00 mol H2O)                   ps: 28.01 g H₂O
print(1.00 mol H2O + 10.00 g H2O + 1.00 mol H2O)    ps: 2.56 mol H₂O
print(1.00 mol H2O + 20.00 g H2O -> atom)           ps: 1.27×10²⁴ atom H₂O
```

Notice that significant digits is preserved throughout the operation. Finally, it automatically balances chemical equation for you:

```ch
print(50.00 g NaOH :CuSO4 + NaOH -> Cu(OH)2 + Na2SO4:-> CuSO4 -> g)     ps: 99.76 g CuSO₄
print(16.00 mol C4H10 :C4H10 + O2 -> CO2 + H2O:-> CO2 -> g)             ps: 2817 g CO₂
```

As this is a programming language with super-cow powers, it can also do other things.

This language support if-else-elif statements:

```ch
gpa = 3.5
exam gpa > 3.5 
    print("A+") 
makeup gpa > 3.0 
    print("A") 
fail 
    print("F")
```

It also supports looping:

```ch
i = 10
during i >= 0
    print(i)
    i -= 1

redo i of 1...11
    print(i)
```

As well as recursion:

```ch
work move(n, from, buf, to)
  exam n == 1
      print(s"Move {n} from {from} to {to}")
  fail
      move(n - 1, from, to, buf)
      move(1, from, buf, to)
      move(n - 1, buf, from, to)
move(3, 'a', 'b', 'c')
```

And even better, closure:

```ch
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

It can format strings:

```ch
name = "Yubo"
print(s"Hello, {name}!")
```

And some basic IO operations, like write to file:

```ch
redo i of 1...10
    redo j of 1...10
        print(s'{i} x {j}
' -> |test.txt|)
```

From the technical aspect, this language is implemented with Python with a hand-made recursive descent parser. It also integrates with `pytest` for testing.