work sum(n)
    exam n == 0
        submit 0
    fail
        submit sum(n-1) + n
print(sum(10))