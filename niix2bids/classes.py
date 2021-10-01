import os    # for path management
import json  # json file loading


########################################################################################################################
class File:

    instances = []

    def __init__(self, path: str):
        self.path = path
        self.__class__.instances.append(self)

    def __repr__(self):
        return f"<{__name__}.{self.__class__.__name__}: path = {self.path}>"


########################################################################################################################
class Nii(File):

    instances = []


########################################################################################################################
class Json(File):

    instances = []


########################################################################################################################
class Volume:

    instances = []

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self, path: str):

        # separate name and extension
        name, ext = os.path.splitext(path)
        if ext != ".nii":
            raise RuntimeError(f"not a .nii file : {path}")

        # instance filling
        self.nii = Nii(path)
        self.json = Json(name + ".json")
        self.seqparam = dict
        self.bidsfields = {}

        # store a list of all instances
        self.__class__.instances.append(self)

    # ------------------------------------------------------------------------------------------------------------------
    def load_json(self):
        with open(self.json.path, "r") as file:
            self.seqparam = json.load(file)  # load the .json content as dict
            self.seqparam['Volume'] = self   # save also in the dict a pointer to the object itself

    # ------------------------------------------------------------------------------------------------------------------
    def __repr__(self):
        return f"<{__name__}.{self.__class__.__name__}: path = {self.nii.path}>"
