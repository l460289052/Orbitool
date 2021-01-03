from multiprocessing import Process, Queue


if __name__ == "__main__":
    call = Queue()
    ret = Queue()

    import Frontground
    main = Frontground.Redirector(call, ret)
    
    import BackgroundProcessor
    back = Process(target=BackgroundProcessor.Processor().routine, args=(call, ret))
    back.start()

    print(main.get_a())
    main.quit()
    





