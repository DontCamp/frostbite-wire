if __name__ == '__main__':
    import os
    from unittest import defaultTestLoader, main

    dir = os.path.dirname(os.path.abspath(__file__))
    defaultTestLoader.discover(dir)
    main('tests')
