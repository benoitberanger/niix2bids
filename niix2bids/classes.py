import os    # for path management
import json  # json file loading

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
    def __init__(self, niipath: str):

        # separate name and extension
        root, ext = os.path.splitext(niipath)
        if ext not in [".nii", ".gz"]:
            raise RuntimeError(f"not a .nii file : {niipath}")
        if ext == ".gz":
            basename = os.path.splitext(os.path.basename(root))[0]
            ext      = '.nii.gz'
            jsonfile = os.path.splitext(root)[0] + ".json"
        else:
            basename = os.path.splitext(os.path.basename(niipath))[0]
            ext      = '.nii'
            jsonfile = os.path.splitext(niipath)[0] + ".json"

        # instance filling
        self.basename         = basename       # /path/to/volume
        self.ext              = ext            # .nii OR .nii.gz
        self.nii              = Nii(niipath)
        self.json             = Json(jsonfile)
        self.seqparam         = dict           # content of the .json file, from dcm2niix
        self.reason_not_ready = ''             # if ready==False, this is the message that will be displayed
        self.bidsfields       = {}             # all bids fields, such as acq-<>_run-<>
        self.tag              = ''             # modality, such as anat, dwi, bold, fmap
        self.sub              = ''             # subject name, such as sub-<>
        self.ses              = ''             # session number, such as sess-<>
        self.suffix           = ''             # suffix, such as T1w, bold, sbref

        # store a list of all instances
        self.__class__.instances.append(self)

    # ------------------------------------------------------------------------------------------------------------------
    def load_json(self):
        with open(self.json.path, "r") as file:
            content = file.read()
            clean = content.replace(r'\\', r'_')  # in ~2021, dcm2iix escaping character changed from _ to \\
            self.seqparam = json.loads(clean)     # load the .json content as dict
            self.seqparam['Volume'] = self        # save also in the dict a pointer to the object itself

    # ------------------------------------------------------------------------------------------------------------------
    def __repr__(self):
        return f"<{__name__}.{self.__class__.__name__}: path = {self.nii.path}>"

    # ------------------------------------------------------------------------------------------------------------------
    def check_if_bval_exists(self) -> bool:
        root, ext = os.path.splitext(self.nii.path)
        if ext == ".gz":
            bval_file = os.path.splitext(root)[0] + ".bval"
        else:
            bval_file = os.path.splitext(self.nii.path)[0] + ".bval"
        if not os.path.exists(bval_file):
            return False
        else:
            self.bval = Bval(bval_file)
            return True

    # ------------------------------------------------------------------------------------------------------------------
    def check_if_bvec_exists(self) -> bool:
        root, ext = os.path.splitext(self.nii.path)
        if ext == ".gz":
            bvec_file = os.path.splitext(root)[0] + ".bvec"
        else:
            bvec_file = os.path.splitext(self.nii.path)[0] + ".bvec"
        if not os.path.exists(bvec_file):
            return False
        else:
            self.bvec = Bvec(bvec_file)
            return True

    # ------------------------------------------------------------------------------------------------------------------
    def __lt__(self, other):
        return self.__repr__()< other.__repr__()

    def __gt__(self, other):
        return self.__repr__() > other.__repr__()
