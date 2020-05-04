# -*- coding: latin-1 -*-
import unittest

import comtypes.test
comtypes.test.requires("ui")

import datetime

from comtypes.client import CreateObject

xlRangeValueDefault = 10
xlRangeValueXMLSpreadsheet = 11
xlRangeValueMSPersistXML = 12

class Test(unittest.TestCase):

    def test_earlybound(self):
        self._doit(False)

    def test_latebound(self):
        self._doit(True)

    def _doit(self, dynamic):
        self.xl = CreateObject("Excel.Application", dynamic=dynamic)

        xl = self.xl
        xl.Visible = 0
        self.assertEqual(xl.Visible, False)
        xl.Visible = 1
        self.assertEqual(xl.Visible, True)

        wb = xl.Workbooks.Add()

        # Test with empty-tuple argument
        xl.Range["A1", "C1"].Value[()] = (10,"20",31.4)
        xl.Range["A2:C2"].Value[()] = ('x','y','z')
        # Test with empty slice argument
        xl.Range["A3:C3"].Value[:] = ('3','2','1')
## not (yet?) implemented:
##        xl.Range["A4:C4"].Value = ('3','2','1')

        # call property to retrieve value
        self.assertEqual(xl.Range["A1:C3"].Value(),
                             ((10.0, 20.0, 31.4),
                              ("x", "y", "z"),
                              (3.0, 2.0, 1.0)))
        # index with empty tuple
        self.assertEqual(xl.Range["A1:C3"].Value[()],
                             ((10.0, 20.0, 31.4),
                              ("x", "y", "z"),
                              (3.0, 2.0, 1.0)))
        # index with empty slice
        self.assertEqual(xl.Range["A1:C3"].Value[:],
                             ((10.0, 20.0, 31.4),
                              ("x", "y", "z"),
                              (3.0, 2.0, 1.0)))
        self.assertEqual(xl.Range["A1:C3"].Value[xlRangeValueDefault],
                             ((10.0, 20.0, 31.4),
                              ("x", "y", "z"),
                              (3.0, 2.0, 1.0)))
        self.assertEqual(xl.Range["A1", "C3"].Value[()],
                             ((10.0, 20.0, 31.4),
                              ("x", "y", "z"),
                              (3.0, 2.0, 1.0)))

        r = xl.Range["A1:C3"]
        i = iter(r)

        # Test for iteration support in 'Range' interface
        self.assertEqual([c.Value() for c in xl.Range["A1:C3"]],
                             [10.0, 20.0, 31.4,
                              "x", "y", "z",
                              3.0, 2.0, 1.0])

        # With pywin32, one could write xl.Cells(a, b)
        # With comtypes, one must write xl.Cells.Item(1, b)

        for i in range(20):
            xl.Cells.Item[i+1,i+1].Value[()] = "Hi %d" % i
            print(xl.Cells.Item[i+1, i+1].Value[()])

        for i in range(20):
            xl.Cells(i+1,i+1).Value[()] = "Hi %d" % i
            print(xl.Cells(i+1, i+1).Value[()])

        # test dates out with Excel
        xl.Range["A5"].Value[()] = "Excel time"
        xl.Range["B5"].Formula = "=Now()"
        self.assertEqual(xl.Cells.Item[5,2].Formula, "=NOW()")

        xl.Range["A6"].Calculate()
        excel_time = xl.Range["B5"].Value[()]
        self.assertEqual(type(excel_time), datetime.datetime)
        python_time = datetime.datetime.now()

        self.assertTrue(python_time >= excel_time)
        self.assertTrue(python_time - excel_time < datetime.timedelta(seconds=1))

        # some random code, grabbed from c.l.p
        sh = wb.Worksheets[1]

        sh.Cells.Item[1,1].Value[()] = "Hello World!"
        sh.Cells.Item[3,3].Value[()] = "Hello World!"
        sh.Range[sh.Cells.Item[1,1],sh.Cells.Item[3,3]].Copy(sh.Cells.Item[4,1])
        sh.Range[sh.Cells.Item[4,1],sh.Cells.Item[6,3]].Select()

    def tearDown(self):
        # Close all open workbooks without saving, then quit excel.
        for wb in self.xl.Workbooks:
            wb.Close(0)
        self.xl.Quit()

if __name__ == "__main__":
    unittest.main()
