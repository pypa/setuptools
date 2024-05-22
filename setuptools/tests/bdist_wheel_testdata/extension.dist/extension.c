#include <Python.h>

static PyMethodDef methods[] = {
	{ NULL, NULL, 0, NULL }
};

static struct PyModuleDef module_def = {
	PyModuleDef_HEAD_INIT,
	"extension",
	"Dummy extension module",
	-1,
	methods
};

PyMODINIT_FUNC PyInit_extension(void) {
	return PyModule_Create(&module_def);
}
