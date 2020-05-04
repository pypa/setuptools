import sys
import unittest
import doctest

from comtypes.test import requires

# This test is unreliable...
requires("events")

class EventsTest(unittest.TestCase):

    def test(self):
        import comtypes.test.test_showevents
        doctest.testmod(comtypes.test.test_showevents, optionflags=doctest.ELLIPSIS)

    # These methods are never called, they only contain doctests.
    if sys.version_info >= (3, 0):
        def IE_ShowEvents(self):
            '''
            >>> from comtypes.client import CreateObject, ShowEvents, PumpEvents
            >>>
            >>> o = CreateObject("InternetExplorer.Application")
            >>> con = ShowEvents(o)
            # event found: DWebBrowserEvents2_StatusTextChange
            # event found: DWebBrowserEvents2_ProgressChange
            # event found: DWebBrowserEvents2_CommandStateChange
            # event found: DWebBrowserEvents2_DownloadBegin
            # event found: DWebBrowserEvents2_DownloadComplete
            # event found: DWebBrowserEvents2_TitleChange
            # event found: DWebBrowserEvents2_PropertyChange
            # event found: DWebBrowserEvents2_BeforeNavigate2
            # event found: DWebBrowserEvents2_NewWindow2
            # event found: DWebBrowserEvents2_NavigateComplete2
            # event found: DWebBrowserEvents2_DocumentComplete
            # event found: DWebBrowserEvents2_OnQuit
            # event found: DWebBrowserEvents2_OnVisible
            # event found: DWebBrowserEvents2_OnToolBar
            # event found: DWebBrowserEvents2_OnMenuBar
            # event found: DWebBrowserEvents2_OnStatusBar
            # event found: DWebBrowserEvents2_OnFullScreen
            # event found: DWebBrowserEvents2_OnTheaterMode
            # event found: DWebBrowserEvents2_WindowSetResizable
            # event found: DWebBrowserEvents2_WindowSetLeft
            # event found: DWebBrowserEvents2_WindowSetTop
            # event found: DWebBrowserEvents2_WindowSetWidth
            # event found: DWebBrowserEvents2_WindowSetHeight
            # event found: DWebBrowserEvents2_WindowClosing
            # event found: DWebBrowserEvents2_ClientToHostWindow
            # event found: DWebBrowserEvents2_SetSecureLockIcon
            # event found: DWebBrowserEvents2_FileDownload
            # event found: DWebBrowserEvents2_NavigateError
            # event found: DWebBrowserEvents2_PrintTemplateInstantiation
            # event found: DWebBrowserEvents2_PrintTemplateTeardown
            # event found: DWebBrowserEvents2_UpdatePageStatus
            # event found: DWebBrowserEvents2_PrivacyImpactedStateChange
            # event found: DWebBrowserEvents2_NewWindow3
            >>> res = o.Navigate2("http://www.python.org")
            Event DWebBrowserEvents2_PropertyChange(None, '{265b75c1-4158-11d0-90f6-00c04fd497ea}')
            Event DWebBrowserEvents2_BeforeNavigate2(None, <POINTER(IWebBrowser2) ...>, VARIANT(vt=0x400c, byref('http://www.python.org/')), VARIANT(vt=0x400c, byref(0)), VARIANT(vt=0x400c, byref(None)), VARIANT(vt=0x400c, byref(VARIANT(vt=0x400c, byref(None)))), VARIANT(vt=0x400c, byref(None)), VARIANT(vt=0x400b, byref(False)))
            Event DWebBrowserEvents2_DownloadBegin(None)
            Event DWebBrowserEvents2_PropertyChange(None, '{D0FCA420-D3F5-11CF-B211-00AA004AE837}')
            >>> res = PumpEvents(0.01)
            Event DWebBrowserEvents2_CommandStateChange(None, 2, False)
            Event DWebBrowserEvents2_CommandStateChange(None, 1, False)
            >>> res = o.Quit()
            >>> res = PumpEvents(0.01)
            Event DWebBrowserEvents2_OnQuit(None)
            >>>
            '''
    else:
        def IE_ShowEvents(self):
            '''
            >>> from comtypes.client import CreateObject, ShowEvents, PumpEvents
            >>>
            >>> o = CreateObject("InternetExplorer.Application")
            >>> con = ShowEvents(o)
            # event found: DWebBrowserEvents2_StatusTextChange
            # event found: DWebBrowserEvents2_ProgressChange
            # event found: DWebBrowserEvents2_CommandStateChange
            # event found: DWebBrowserEvents2_DownloadBegin
            # event found: DWebBrowserEvents2_DownloadComplete
            # event found: DWebBrowserEvents2_TitleChange
            # event found: DWebBrowserEvents2_PropertyChange
            # event found: DWebBrowserEvents2_BeforeNavigate2
            # event found: DWebBrowserEvents2_NewWindow2
            # event found: DWebBrowserEvents2_NavigateComplete2
            # event found: DWebBrowserEvents2_DocumentComplete
            # event found: DWebBrowserEvents2_OnQuit
            # event found: DWebBrowserEvents2_OnVisible
            # event found: DWebBrowserEvents2_OnToolBar
            # event found: DWebBrowserEvents2_OnMenuBar
            # event found: DWebBrowserEvents2_OnStatusBar
            # event found: DWebBrowserEvents2_OnFullScreen
            # event found: DWebBrowserEvents2_OnTheaterMode
            # event found: DWebBrowserEvents2_WindowSetResizable
            # event found: DWebBrowserEvents2_WindowSetLeft
            # event found: DWebBrowserEvents2_WindowSetTop
            # event found: DWebBrowserEvents2_WindowSetWidth
            # event found: DWebBrowserEvents2_WindowSetHeight
            # event found: DWebBrowserEvents2_WindowClosing
            # event found: DWebBrowserEvents2_ClientToHostWindow
            # event found: DWebBrowserEvents2_SetSecureLockIcon
            # event found: DWebBrowserEvents2_FileDownload
            # event found: DWebBrowserEvents2_NavigateError
            # event found: DWebBrowserEvents2_PrintTemplateInstantiation
            # event found: DWebBrowserEvents2_PrintTemplateTeardown
            # event found: DWebBrowserEvents2_UpdatePageStatus
            # event found: DWebBrowserEvents2_PrivacyImpactedStateChange
            # event found: DWebBrowserEvents2_NewWindow3
            >>> res = o.Navigate2("http://www.python.org")
            Event DWebBrowserEvents2_PropertyChange(None, u'{265b75c1-4158-11d0-90f6-00c04fd497ea}')
            Event DWebBrowserEvents2_BeforeNavigate2(None, <POINTER(IWebBrowser2) ...>, VARIANT(vt=0x400c, byref(u'http://www.python.org/')), VARIANT(vt=0x400c, byref(0)), VARIANT(vt=0x400c, byref(None)), VARIANT(vt=0x400c, byref(VARIANT(vt=0x400c, byref(None)))), VARIANT(vt=0x400c, byref(None)), VARIANT(vt=0x400b, byref(False)))
            Event DWebBrowserEvents2_DownloadBegin(None)
            Event DWebBrowserEvents2_PropertyChange(None, u'{D0FCA420-D3F5-11CF-B211-00AA004AE837}')
            >>> res = PumpEvents(0.01)
            Event DWebBrowserEvents2_CommandStateChange(None, 2, False)
            Event DWebBrowserEvents2_CommandStateChange(None, 1, False)
            >>> res = o.Quit()
            >>> res = PumpEvents(0.01)
            Event DWebBrowserEvents2_OnQuit(None)
            >>>
            '''
        
    def IE_GetEvents():
        """
        >>> from comtypes.client import CreateObject, GetEvents, PumpEvents
        >>>
        >>> o =  CreateObject("InternetExplorer.Application")
        >>> class EventHandler(object):
        ...     def DWebBrowserEvents2_PropertyChange(self, this, what):
        ...         print("PropertyChange: %s" % what)
        ...         return 0
        ...
        >>>
        >>> con = GetEvents(o, EventHandler())
        >>> res = o.Navigate2("http://www.python.org")
        PropertyChange: {265b75c1-4158-11d0-90f6-00c04fd497ea}
        PropertyChange: {D0FCA420-D3F5-11CF-B211-00AA004AE837}
        >>> res = o.Quit()
        >>> res = PumpEvents(0.01)
        >>>
        """

    def Excel_Events(self):
        '''
        >>> from comtypes.client import CreateObject, ShowEvents, PumpEvents
        >>>
        >>> o = CreateObject("Excel.Application")
        >>> con = ShowEvents(o)
        # event found: AppEvents_NewWorkbook
        # event found: AppEvents_SheetSelectionChange
        # event found: AppEvents_SheetBeforeDoubleClick
        # event found: AppEvents_SheetBeforeRightClick
        # event found: AppEvents_SheetActivate
        # event found: AppEvents_SheetDeactivate
        # event found: AppEvents_SheetCalculate
        # event found: AppEvents_SheetChange
        # event found: AppEvents_WorkbookOpen
        # event found: AppEvents_WorkbookActivate
        # event found: AppEvents_WorkbookDeactivate
        # event found: AppEvents_WorkbookBeforeClose
        # event found: AppEvents_WorkbookBeforeSave
        # event found: AppEvents_WorkbookBeforePrint
        # event found: AppEvents_WorkbookNewSheet
        # event found: AppEvents_WorkbookAddinInstall
        # event found: AppEvents_WorkbookAddinUninstall
        # event found: AppEvents_WindowResize
        # event found: AppEvents_WindowActivate
        # event found: AppEvents_WindowDeactivate
        # event found: AppEvents_SheetFollowHyperlink
        # event found: AppEvents_SheetPivotTableUpdate
        # event found: AppEvents_WorkbookPivotTableCloseConnection
        # event found: AppEvents_WorkbookPivotTableOpenConnection
        # event found: AppEvents_WorkbookSync
        # event found: AppEvents_WorkbookBeforeXmlImport
        # event found: AppEvents_WorkbookAfterXmlImport
        # event found: AppEvents_WorkbookBeforeXmlExport
        # event found: AppEvents_WorkbookAfterXmlExport
        >>> wb = o.Workbooks.Add()
        Event AppEvents_NewWorkbook(None, <POINTER(_Workbook) ...>)
        Event AppEvents_WorkbookActivate(None, <POINTER(_Workbook) ...>)
        Event AppEvents_WindowActivate(None, <POINTER(_Workbook) ...>, <POINTER(Window) ...>)
        >>> PumpEvents(0.1)
        >>> res = o.Quit(); PumpEvents(0.1)
        Event AppEvents_WorkbookBeforeClose(None, <POINTER(_Workbook) ...>, VARIANT(vt=0x400b, byref(False)))
        Event AppEvents_WindowDeactivate(None, <POINTER(_Workbook) ...>, <POINTER(Window) ...>)
        Event AppEvents_WorkbookDeactivate(None, <POINTER(_Workbook) ...>)
        >>>
        '''

    def Excel_Events_2(self):
        '''
        >>> from comtypes.client import CreateObject, GetEvents, PumpEvents
        >>>
        >>> o = CreateObject("Excel.Application")
        >>> class Sink(object):
        ...    def AppEvents_NewWorkbook(self, this, workbook):
        ...        print("AppEvents_NewWorkbook %s" % workbook)
        ...
        >>>
        >>> con = GetEvents(o, Sink())
        >>> wb = o.Workbooks.Add()
        AppEvents_NewWorkbook <POINTER(_Workbook) ...>
        >>>
        >>> class Sink(object):
        ...    def AppEvents_NewWorkbook(self, workbook):
        ...        print("AppEvents_NewWorkbook(no this) %s" % workbook)
        ...
        >>>
        >>> con = GetEvents(o, Sink())
        >>> wb = o.Workbooks.Add()
        AppEvents_NewWorkbook(no this) <POINTER(_Workbook) ...>
        >>>
        >>> res = o.Quit()
        >>>
        '''

    def Word_Events(self):
        '''
        >>> from comtypes.client import CreateObject, ShowEvents, PumpEvents
        >>>
        >>> o = CreateObject("Word.Application")
        >>> con = ShowEvents(o)
        # event found: ApplicationEvents4_Startup
        # event found: ApplicationEvents4_Quit
        # event found: ApplicationEvents4_DocumentChange
        # event found: ApplicationEvents4_DocumentOpen
        # event found: ApplicationEvents4_DocumentBeforeClose
        # event found: ApplicationEvents4_DocumentBeforePrint
        # event found: ApplicationEvents4_DocumentBeforeSave
        # event found: ApplicationEvents4_NewDocument
        # event found: ApplicationEvents4_WindowActivate
        # event found: ApplicationEvents4_WindowDeactivate
        # event found: ApplicationEvents4_WindowSelectionChange
        # event found: ApplicationEvents4_WindowBeforeRightClick
        # event found: ApplicationEvents4_WindowBeforeDoubleClick
        # event found: ApplicationEvents4_EPostagePropertyDialog
        # event found: ApplicationEvents4_EPostageInsert
        # event found: ApplicationEvents4_MailMergeAfterMerge
        # event found: ApplicationEvents4_MailMergeAfterRecordMerge
        # event found: ApplicationEvents4_MailMergeBeforeMerge
        # event found: ApplicationEvents4_MailMergeBeforeRecordMerge
        # event found: ApplicationEvents4_MailMergeDataSourceLoad
        # event found: ApplicationEvents4_MailMergeDataSourceValidate
        # event found: ApplicationEvents4_MailMergeWizardSendToCustom
        # event found: ApplicationEvents4_MailMergeWizardStateChange
        # event found: ApplicationEvents4_WindowSize
        # event found: ApplicationEvents4_XMLSelectionChange
        # event found: ApplicationEvents4_XMLValidationError
        # event found: ApplicationEvents4_DocumentSync
        # event found: ApplicationEvents4_EPostageInsertEx
        >>> PumpEvents(0.1)
        >>> doc = o.Documents.Add()
        Event ApplicationEvents4_NewDocument(None, <POINTER(_Document) ...>)
        Event ApplicationEvents4_DocumentChange(None)
        >>> res = o.Quit(); PumpEvents(0.1)
        Event ApplicationEvents4_DocumentBeforeClose(None, <POINTER(_Document) ...>, VARIANT(vt=0x400b, byref(False)))
        Event ApplicationEvents4_WindowDeactivate(None, <POINTER(_Document) ...>, <POINTER(Window) ...>)
        Event ApplicationEvents4_DocumentChange(None)
        Event ApplicationEvents4_Quit(None)
        >>>
        '''

if __name__ == "__main__":
    unittest.main()
