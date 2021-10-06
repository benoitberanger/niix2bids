import os  # for path management
import json  # json file loading
import logging  # logging lib (terminal & file)

# get logger with current name
log = logging.getLogger(__name__)


########################################################################################################################
class File:
    instances = []

    def __init__(self, path: str):

        # instance filling
        self.path = path

        # store a list of all instances
        self.__class__.instances.append(self)  # add in a class variable all instances of the class, for easy retrieve

    def __repr__(self):
        return f"<{__name__}.{self.__class__.__name__}: path = {self.path}>"


########################################################################################################################
class Nii(File):
    instances = []


########################################################################################################################
class Json(File):
    instances = []


########################################################################################################################
class Bval(File):
    instances = []


########################################################################################################################
class Bvec(File):
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
        self.nii        = Nii(path)
        self.json       = Json(name + ".json")
        self.seqparam   = dict
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

    # ------------------------------------------------------------------------------------------------------------------
    def check_if_bval_exists(self) -> bool:
        bval_file = os.path.splitext(self.nii.path)[0] + ".bval"
        if not os.path.exists(bval_file):
            log.warning(f"this file has no .bval associated : {self.nii.path}")
            return False
        self.bval = Bval(bval_file)
        return True

    # ------------------------------------------------------------------------------------------------------------------
    def check_if_bvec_exists(self) -> bool:
        bvec_file = os.path.splitext(self.nii.path)[0] + ".bvec"
        if not os.path.exists(bvec_file):
            log.warning(f"this file has no .bvec associated : {self.nii.path}")
            return False
        self.bvec = Bvec(bvec_file)
        return True
