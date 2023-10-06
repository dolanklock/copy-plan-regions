
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


clr.AddReference("RevitServices")
import RevitServices
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

uiapp = __revit__
# uiapp = DocumentManager.Instance.CurrentUIApplication
app = uiapp.Application
uidoc = uiapp.ActiveUIDocument
doc = uiapp.ActiveUIDocument.Document

import sys
sys.path.append("G:\My Drive\PythonScripts\GD_PythonResources\Revit")


from pyrevit import forms
import math
from GetSetParameters import *
from System.Collections.Generic import List
import Selection
import Schedules
from rpw import db
import csv
import GUI
from pyrevit import forms

# CODE BELOW HERE #

__author__ = "Dolan Klock"

# Tooltip
__doc__ = "This tool sets checks on annotation crop boundary parameter and matches the crop boundary for annotation" \
          " crop boundary of the selected source view to all views with the same scope box as the source view chosen"


"""
plan
- USE THIS ONE FOR NOW - give option to have user prompt for list of views or by selection in project browser(for selection add in yellow bar at top for seleciton if can)
- ask user to copy/replace all plan regions from source view to all views that share the same level
- ask user to copy/replace all plan regions from source view to all views that share the same level and same scope box
- ask user to copy/replace all plan regions from source view to all selected views in browser

- (might be different script) option to select specific 2d items in source view to copy to all select views or views at same level or views with same level and scope box
"""

all_views = Selection.GetElementsFromDoc.all_views(doc, elements_only=True)

all_view_plans = list(filter(lambda x: x.ViewType == DB.ViewType.FloorPlan or x.ViewType == DB.ViewType.AreaPlan, all_views))
# all_views_plans = [view for view in all_views if view.ViewType == DB.ViewType.FloorPlan or view.ViewType == DB.ViewType.AreaPlan]
all_views_ceilplans = list(filter(lambda x: x.ViewType == DB.ViewType.CeilingPlan, all_views))
# all_views_ceilplans = [view for view in all_views if view.ViewType == DB.ViewType.CeilingPlan]


def view_selection_project_browser():
    element_ids = uidoc.Selection.GetElementIds()
    return [doc.GetElement(e_id) for e_id in element_ids]

def set_category_visibility(view, category_id, is_hidden):
    """Sets view or view templates category visibility

    Args:
        view_template (_type_): _description_
        category_id (_type_): _description_
        is_hidden (bool): _description_
    """
    with db.Transaction("Change view category visibility"):
        view.SetCategoryHidden(category_id, is_hidden)

def get_plan_regions_in_view(doc, s_view):
    """gets all plan regions in view

    Args:
        doc (_type_): _description_
        view (_type_): _description_

    Returns:
        _type_: _description_
    """
    all_plan_regions_in_view_fec = DB.FilteredElementCollector(doc, s_view.Id).OfCategory(DB.BuiltInCategory.OST_PlanRegion).WhereElementIsNotElementType()
    all_plan_rergions_in_view = [pl for pl in all_plan_regions_in_view_fec]
    return all_plan_rergions_in_view

def copy_plan_regions(source_view, dest_view, plan_regions_copy):
    # print(source_view.Name, dest_view.Name)
    plan_regions_delete = get_plan_regions_in_view(doc, dest_view)
    for pl in plan_regions_delete:
        with db.Transaction("Delete plan region"):
            doc.Delete(pl.Id)
    # create ICollection
    plan_regions_collection = List[DB.ElementId]()
    for i in plan_regions_copy:
        plan_regions_collection.Add(i.Id)
    with db.Transaction("Copy plan regions"):
        DB.ElementTransformUtils.CopyElements(sourceView=source_view,
                                               elementsToCopy=plan_regions_collection,
                                                 destinationView=dest_view,
                                                   additionalTransform=DB.Transform.Identity,
                                                     options=DB.CopyPasteOptions())

def view_temp_override(arg, enable=True):
    if enable:
        with db.Transaction("enable temporary overrides"):
            arg.EnableTemporaryViewPropertiesMode(arg.ViewTemplateId)
    else:
        with db.Transaction("disable temporary overrides"):
            arg.DisableTemporaryViewMode(DB.TemporaryViewMode.TemporaryViewProperties)

def view_crop_boundary_visible(view, visible=False):
    with db.Transaction("change views crop box visibile"):
        view.CropBoxVisible = visible

def view_set_scope_box(view, scope_box_id):
    if scope_box_id is None:
        vsb_param = view.LookupParameter("Scope Box")
        with db.Transaction("Setting view scope box"):
            vsb_param.Set(DB.ElementId(-1))
    else:
        vsb_param = view.LookupParameter("Scope Box")
        with db.Transaction("Setting view scope box"):
            vsb_param.Set(scope_box_id)

def view_crop_active(view, active=False):
    with db.Transaction("change view crop"):
        view.CropBoxActive = active

def prep_view(fn, view, **kwargs):
    # TODO: check if view is cropped or not and return back to original state
    print(view.LookupParameter("Scope Box"))
    vsb_element_id = view.LookupParameter("Scope Box").AsElementId()
    if str(vsb_element_id) != "-1": # checks if view has scope box
        # set scope box to none
        view_set_scope_box(view, scope_box_id=None)
        print(view.ViewTemplateId)
        # uncrop view
        view_crop_active(view, active=False)
        # enable temp overrides
        if str(view.ViewTemplateId) != "-1":  # check if view template is applied to the source_view
            view_temp_override(view, enable=True)
            # turing on plan region category in view
            set_category_visibility(view, category_id=Selection.get_category_by_name("Plan Region").Id, is_hidden=False)
            rv = fn(**kwargs)
            view_temp_override(view, enable=False)
            view_set_scope_box(view, scope_box_id=vsb_element_id)  # setting scope box back to original
            view_crop_boundary_visible(view, visible=False)
        else:
            # if view does not have view template assigned
            # turing on plan region category in view
            set_category_visibility(view, category_id=Selection.get_category_by_name("Plan Region").Id, is_hidden=False)
            rv = fn(**kwargs)
            # hiding plan region when done
            set_category_visibility(view, category_id=Selection.get_category_by_name("Plan Region").Id, is_hidden=True)
            view_set_scope_box(view, scope_box_id=vsb_element_id)
            view_crop_boundary_visible(view, visible=False)
    else:
        # if does not have scope box
        # uncrop view
        crop_box_state = view.CropBoxActive
        if crop_box_state:
            view_crop_active(view, active=False)
        # check if view has view template
        if str(view.ViewTemplateId) != "-1":  # check if view template is applied to the source_view
            view_temp_override(view, enable=True)
            set_category_visibility(view, category_id=Selection.get_category_by_name("Plan Region").Id, is_hidden=False)
            rv = fn(**kwargs)
            view_temp_override(view, enable=False)
            if crop_box_state:
                view_crop_active(view, active=True)
                view_crop_boundary_visible(view, visible=False)
        else:
            # if view does not have view template assigned
            # turing on plan region category in view
            set_category_visibility(view, category_id=Selection.get_category_by_name("Plan Region").Id, is_hidden=False)
            rv = fn(**kwargs)
            # hiding plan region when done
            set_category_visibility(view, category_id=Selection.get_category_by_name("Plan Region").Id, is_hidden=True)
            if crop_box_state:
                view_crop_active(view, active=True)
                view_crop_boundary_visible(view, visible=False)

    return rv


def main():
    # check user has active view open that has correct plan regions
    if GUI.UI_two_options(title="Active View", main_instruction="Do you have the active view open that has correct plan regions to copy?", commandlink1="Yes proceed", commandlink2="No, stop script and I will have active view open next time"):
        if GUI.UI_two_options(title="Plan Regions Copy",
                            main_instruction="Select views from list or by selected views in browser?",
                            commandlink1="Select From List", commandlink2="Select From Project Browser"):
            # getting user selected views for plan regions to replace in
            all_views_plan_ceil = list(filter(lambda x: x.ViewType == DB.ViewType.FloorPlan or x.ViewType == DB.ViewType.AreaPlan or x.ViewType == DB.ViewType.CeilingPlan, all_views))
            t_dict = {view.Name: view for view in all_views_plan_ceil}
            chosen_views = forms.SelectFromList.show(sorted(list(t_dict.keys()), key=lambda x: x[0]), title="Select the views to replace plan region in", multiselect=True)
            chosen_views = [t_dict[val] for val in chosen_views]
            # for i in chosen_views:
            #     print(i.LookupParameter("View Name").AsString())
            # print()
            # print(chosen_views)
            correct_plan_regions = prep_view(get_plan_regions_in_view, doc.ActiveView, doc=doc, s_view=doc.ActiveView)
            for dest_view in chosen_views:
                # print(dest_view.Name)
                # correct_plan_regions = prep_view(get_plan_regions_in_view, doc.ActiveView, doc=doc, s_view=doc.ActiveView)
                prep_view(copy_plan_regions, dest_view, source_view=doc.ActiveView, dest_view=dest_view, plan_regions_copy=correct_plan_regions)
        else:
            element_ids = uidoc.Selection.GetElementIds()
            # Check entry not empty
            if len(element_ids) == 0:
                forms.alert("Re-run script and make sure you have views selected from project browser")
                sys.exit()
            # check types of elements selected
            for e_id in element_ids:
                e = doc.GetElement(e_id)
                if not isinstance(e, DB.View) or type(e) == DB.ViewSheet:
                    forms.alert("Please only select views")
                    sys.exit()
            chosen_views = [doc.GetElement(e_id) for e_id in element_ids]
            # for v in chosen_views:
            #     print(v)
            # getting user selected views for plan regions to replace in
            all_views_plan_ceil = list(filter(lambda x: x.ViewType == DB.ViewType.FloorPlan or x.ViewType == DB.ViewType.AreaPlan or x.ViewType == DB.ViewType.CeilingPlan, all_views))
            correct_plan_regions = prep_view(get_plan_regions_in_view, doc.ActiveView, doc=doc, s_view=doc.ActiveView)
            for dest_view in chosen_views:
                prep_view(copy_plan_regions, dest_view, source_view=doc.ActiveView, dest_view=dest_view, plan_regions_copy=correct_plan_regions)
    else:
        sys.exit()


if __name__ == "__main__":
    main()




# def prep_view(source_view, dest_view, plan_regions_copy):
#     """this function checks source view settings and preps it for copying plan regions to dest views.
#     Deletes plan regions in dest views and copies correct ones to dest view

#     Args:
#         view (_type_): _description_
#     """
#     # check if view has scope box assigned
#     vsb_element_id = source_view.LookupParameter("Scope Box").AsElementId()
#     if str(vsb_element_id) != "-1":
#         print("true")
#         vsb_param = source_view.LookupParameter("Scope Box")
#         print(vsb_param)
#         # set scope box to none
#         with db.Transaction("Setting view scope box to none"):
#             vsb_param.Set(DB.ElementId(-1))
#         # uncrop source_view
#         with db.Transaction("Uncrop view"):
#             source_view.CropBoxActive = False
#         # enable temp overrides
#         view_has_template = True
#         if str(source_view.ViewTemplateId) != "-1":  # check if view template is applied to the source_view
#             view_has_template = False
#             with db.Transaction("Uncrop view"):
#                 source_view.EnableTemporaryViewPropertiesMode(source_view.ViewTemplateId)
#         # turing on plan region category in view
#         set_category_visibility(source_view, category_id=Selection.get_category_by_name("Plan Region").Id, is_hidden=False)
#         # get plan regions in view and delete them and then copy correct plan region in the view
#         plan_regions_delete = get_plan_regions_in_view(doc, dest_view)
#         for pl in plan_regions_delete:
#             with db.Transaction("Delete plan region"):
#                 doc.Delete(pl.Id)
#         # copying correct plan regions to view
#         with db.Transaction("Copy plan regions"):
#             DB.ElementTransformUtils.CopyElements(source_view,
#                                                 plan_regions_copy,
#                                                 dest_view,
#                                                 DB.Transform.Identity,
#                                                 options=DB.CopyPasteOptions(),
#                                                 )