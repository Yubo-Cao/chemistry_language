work fib(n)
    exam n <= 1
        submit 1
    fail
        res = fib(n-1) + fib(n-2)
        submit fib(n - 1) + fib(n - 2)

redo i of 1...20
    print(s'fib({i}) = {fib(i)}')