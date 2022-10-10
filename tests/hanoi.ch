work move(n, from, buf, to)
    exam n == 1
        print(s"Move {n} from {from} to {to}")
    fail
        move(n - 1, from, to, buf)
        move(1, from, buf, to)
        move(n - 1, buf, from, to)
move(3, 'a', 'b', 'c')