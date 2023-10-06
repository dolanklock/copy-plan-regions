import clr
clr.AddReferenceByPartialName('PresentationCore')
clr.AddReferenceByPartialName('AdWindows')
clr.AddReferenceByPartialName("PresentationFramework")
clr.AddReferenceByPartialName('System')
clr.AddReferenceByPartialName('System.Windows.Forms')

from Autodesk.Revit import DB
from Autodesk.Revit import UI
import Autodesk
import Autodesk.Windows as aw

uiapp = __revit__
uidoc = uiapp.ActiveUIDocument
doc = uiapp.ActiveUIDocument.Document

from pyrevit import forms

# CODE BELOW HERE #


class OptionsLineStyle(forms.TemplateListItem):
    @property
    def name(self):
        return self.Name

def UI_two_options(title="", main_instruction="", commandlink1="", commandlink2=""):
    """UI prompt for user to input the two command options in UI dialog. Will return True if command1link chosen
    else returns False

    Args:
        title (_type_): _description_
        main_instruction (_type_): _description_
        commandlink1 (str, optional): Input the string you would like user to see for option 1
        commandlink2 (str, optional): Input the string you would like user to see for option 2

    Returns:
        Bool: Returns True if commandlink1 chosen else returns Falsee
    """
    task_dialog = Autodesk.Revit.UI.TaskDialog(title)
    task_dialog.CommonButtons = Autodesk.Revit.UI.TaskDialogCommonButtons.Ok
    task_dialog.MainInstruction = main_instruction
    task_dialog.AddCommandLink(Autodesk.Revit.UI.TaskDialogCommandLinkId.CommandLink1, commandlink1)
    task_dialog.AddCommandLink(Autodesk.Revit.UI.TaskDialogCommandLinkId.CommandLink2, commandlink2)
    result = task_dialog.Show()
    if str(result) == "CommandLink1":
        return True
    return False   

def ask_for_bool(title="", main_instruction=""):
    """Simple UI for prompting user to select true or false

    Args:
        title (str, optional): _description_. Defaults to "".
        main_instruction (str, optional): _description_. Defaults to "".
        commandlink1 (str, optional): _description_. Defaults to "Yes".
        commandlink2 (str, optional): _description_. Defaults to "No".

    Returns:
        _type_: "CommandLink1" or "CommandLink2"
    """
    commandlink1="Yes"
    commandlink2="No"
    task_dialog = Autodesk.Revit.UI.TaskDialog(title)
    # task_dialog.AllowCancellation = True
    task_dialog.CommonButtons = Autodesk.Revit.UI.TaskDialogCommonButtons.Ok
    task_dialog.MainInstruction = main_instruction
    task_dialog.AddCommandLink(Autodesk.Revit.UI.TaskDialogCommandLinkId.CommandLink1, commandlink1)
    task_dialog.AddCommandLink(Autodesk.Revit.UI.TaskDialogCommandLinkId.CommandLink2, commandlink2)
    result = task_dialog.Show()
    if str(result) == "CommandLink1":
        return True
    return False    

def user_prompt_get_object_from_names(obj_elements, obj_names, title="", multiselect=False):
    """
    take in the objects and the list of names of the objects that you want to be displayed to the user
    and then orders the objects alphabetically and gets user to select one and then returns selection
    """
    output = []
    obj_names_ordered = sorted(obj_names, key=lambda x: x[0])

    input_obj_names = forms.SelectFromList.show(obj_names_ordered, title=title, multiselect=multiselect)
    for obj in input_obj_names:
        output.append(obj_elements[obj_names.index(obj)])
    if not multiselect:
        return output[0]
    return output
    
def UI_multi_text_input():
    components = [Label("Input the word you want to find and replace"), TextBox("textbox1", Text=""),
                Label("Input the replacement word"), TextBox("textbox2", Text=""),
                Separator(),
                Button('Ok'),
                ]

    form = FlexForm("Sheet Name Find & Replace", components)
    form.show()

    try:
        word_to_replace = form.values['textbox1']
        word_to_replace_with = form.values['textbox2']
    except Exception:
        sys.exit()
    else:
        return word_to_replace, word_to_replace_with
    

if __name__ == "__main__":
    e_id = DB.ElementId(5828568)
    e = doc.GetElement(e_id)

    type_name = GetParameter.get_type_name(e)

    print(type_name)

    SetParameter.set_instance_parameter_value(e, parameter_name='FILLED REGION LEVEL', parameter_value='testing12345')

    b_a = GetParameter.get_instance_parameter_by_name(e, parameter_name="Base Area")

    print(b_a)

    # SetParameter.set_instance_parameter_value(e, 'Isolate Filled Region', 1)

    SetParameter.set_type(e, new_types_id=2331973)

    SetParameter.set_type_mark(e, 'testing')

