Importing, exporting and deleting a survey page
--------------------
.. manipulation buttons
.. |importPage| image:: ../_static/user/impPgButton.png
.. |importButton| image:: ../_static/user/impButton.png
.. |dontImportButton| image:: ../_static/user/dontImpButton.png
.. |browseButton| image:: ../_static/user/browseButton.png
.. |export| image:: ../_static/user/exportButton.png
.. |downXML| image:: ../_static/user/downXML.png
.. |delete| image:: ../_static/user/delButton.png

This section explains how to import a new page on a survey under development, by uploading an external XML file that you or your colleagues might have created. This allows the customisation of the survey pages according to your needs, without necessarily using the default options provided by our survey system. 

We assume that you are in the correct survey and will not show you how to navigate to that, as this process has been covered extensively in previous sections. If you need to refer to that process again, then please see the last paragraph of the *Access PyQuestionnaire* section(:doc:`ref<access_Qnnaire>`).

Importing a page
******************
- While on the home page of your survey (:doc:`ref<glossary>`), click on the |importPage| button, included in the *Manipulation buttons* (:doc:`ref<survey_home_page_elements>`) of that screen.

.. Comment: the line >> :doc:`ref<glossary>` above, allows import_pg.rst to link to the glossary.rst

- The following screen will then appear:

.. image:: ../_static/user/impPgScreen.png
   :align: center
   
- On the appearing screen, click the |browseButton| button and navigate to the XML file you would like to add on your survey. 

- When you have completed the above step, click on the |importButton| button, if you decide that want to import the chosen file, or on the |dontImportButton| button, if you decide you want to discard it.

- By clicking on the |importButton| button, the imported page will appear under the list of pages that your survey already has. As a reminder, the list of pages, entitled **Pages**, is located at the survey's **home page** (:doc:`ref<glossary>`).
   
Exporting a page
****************
Exporting a page works in a similar way to exporting a survey, as shown earlier in the *Importing, exporting, duplicating and deleting an existing survey* section (:doc:`ref<imp_exp_dupl_del_survey>`).

.. _correctSurvPg:

If you are in the survey page you want to export
++++++++++++++++++++++
 a) Click on the |export| button above the survey title.
 
 b) You will then be directed to the *Export* screen, as shown below:

    .. image:: ../_static/user/exportPgScreen.png
       :align: center
	   
 c) To export the XML code of the page, click on the |downXML| button. The relevant XML code will then appear in your browser and you will be able to copy in one of your files.

If you are in a survey page, but not the one you want to export
++++++++++++++++++++++
Let's assume you are in page 2 of your survey, as shown below, but you want to export page 1 instead:

.. image:: ../_static/user/pgTwoScreen.png
   :align: center  

There are two ways to do this:
  a) click on the **Survey** above the page's title.
  
  b) use the **Breadcrumbs**, above the **Survey** button, and click on the title of the Survey. In the above example screenshot, the Survey title would be **Test Survey**.
  
  c) in any case, you will be directed to the survey's **home page** (:doc:`ref<glossary>`).
  
  d) you can click on the link of the survey page you want to export.
  
  e) then follow the instructions (a) to (c) of the :ref:`correctSurvPg` above.
    
Deleting a page
*************** 
Deleting a page is pretty straightforward.

If you are in the survey page you want to delete
++++++++++++++++++++++
  a) click on the |delete| button above the survey title.
  
  b) a message will appear asking you to confirm the deletion.
  
  c) if you are sure you want to delete the page, click **OK**. Otherwise, **Cancel** the request. 
  
  d) if you have clicked **OK**, you will be re-directed to the survey's **home page** (:doc:`ref<glossary>`).
  
If you are in the survey's **home page**
++++++++++++++++++++++  

  a) you will be seeing a list of the available survey pages, under the title **Pages**, as shown below:
  
     Note that the details of each page (i.e. questions included, type of page and next page) and the available buttons are enclosed within a rectangle with dotted borders.
  
  b) find the page you want to delete and click on the |delete| button of that page. 
  
  b) this will prompt a message asking to confirm the deletion.
  
  c) if you are sure you want to delete the page, click **OK**. Otherwise, **Cancel** the request. 
  
  d) As previously, if you have clicked **OK**, you will be re-directed to the survey's **home page** (:doc:`ref<glossary>`).
  
.. admonition:: Next section

   In the next section, we will show you how to test and run a developed survey.