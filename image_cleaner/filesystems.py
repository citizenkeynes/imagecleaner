from pydrive2.fs import GDriveFileSystem
import os
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class GoogleDriveFileSystem:
    def __init__(self, dir="root/lola/scrapes"):
        self.directory = dir
        self.max_par = 30
        self.fs = GDriveFileSystem(
            "root",
            client_id="520373805335-jctrsil46g6gre7kkhll9onvv9a4erjb.apps.googleusercontent.com",
            client_secret="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"
        )
    def walk(self):
        root_subfolders = [f["name"] for f in self.fs.listdir(self.directory) if f["type"]=="directory"]
        def walk_folder(folder):
            print("walk+" + folder)
            return [(a,b,c) for a,b,c in self.fs.walk(folder)]

        results = []
        with ThreadPoolExecutor(max_workers=self.max_par) as executor:
            futures = [executor.submit(walk_folder, folder) for folder in root_subfolders]
            for future in as_completed(futures):
                results.extend(future.result())
        return results
    def remove(self, file_id):
        print("remove+" + file_id)
        thread = threading.Thread(target=self.fs.rm, args=(os.path.join(self.directory, file_id),))
        thread.start()

    def open(self, file_id, mode="r"):
        return self.fs.open(os.path.join(self.directory, file_id), mode)

    def relpath(self, root, filename):
        fp = os.path.join(root, filename)
        return os.path.relpath(fp, self.directory)


class LocalFileSystem:
    def __init__(self,directory):
        self.directory = directory
    def walk(self):
        for a,b,c in os.walk(self.directory):
            yield a,b,c
    def remove(self,file):
        os.remove(os.path.join(self.directory,file))
    def open(self,file,mode="r"):
        return open(os.path.join(self.directory,file),mode)
    def relpath(self,root,filename):
        fp = os.path.join(root,filename)
        return os.path.relpath(fp,self.directory)