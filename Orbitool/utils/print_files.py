from files import FolderTraveler

if __name__ == "__main__":
    ft = FolderTraveler(["utils", "functions"], [".py", ".pyx"], True)
    for file in ft:
        print(file)
