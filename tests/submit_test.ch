work test()
    redo x of 1...10
        exam x % 2 == 0
            print(x)
    submit na

print(test())