# -*- coding: utf-8 -*-

__author__ = "Alan Edmundo Etkin <spametki@gmail.com>"
__copyright__ = "(C) 2024 Alan Edmundo Etkin. GNU GPL 3."

from gluon.sqlhtml import OptionsWidget, add_class

class RadioWidgetAlternative(OptionsWidget):

    @classmethod
    def widget(cls, field, value, **attributes):
        """
        Generates a TABLE tag, including INPUT radios (only 1 option allowed)
        see also: `FormWidget.widget`
        
        Modificación para mostrar option en línea.

        Base: gluon.sqlhtml.RadioWidget de web2py
        """

        if isinstance(value, (list, tuple)):
            value = str(value[0])
        else:
            value = str(value)

        attr = cls._attributes(field, {}, **attributes)
        attr['_class'] = add_class(attr.get('_class'), 'web2py_radiowidget')

        requires = field.requires
        if not isinstance(requires, (list, tuple)):
            requires = [requires]
        if requires:
            if hasattr(requires[0], 'options'):
                options = requires[0].options()
            else:
                raise SyntaxError('widget cannot determine options of %s'
                                  % field)
        
        options = [(k, v) for k, v in options if str(v)]
        
        opts = []
        cols = attributes.get('cols', 1)
        totals = len(options)
        
        mods = totals % cols
        rows = totals // cols
        
        if mods:
            rows += 1

        # widget style
        wrappers = dict(
            table=(TABLE, TR, TD),
            ul=(DIV, UL, LI),
            divs=(DIV, DIV, DIV)
        )
        parent, child, inner = wrappers[attributes.get('style', 'table')]

        for r_index in range(rows):
            tds = []
            for k, v in options[r_index * cols:(r_index + 1) * cols]:
                checked = {'_checked': 'checked'} if k == value else {}
                tds.append(inner(INPUT(_type='radio',
                                       _id='%s%s' % (field.name, k),
                                       _name=field.name,
                                       requires=attr.get('requires', None),
                                       hideerror=True, _value=k,
                                       value=value,
                                       **checked),
                                 LABEL(v, _for='%s%s' % (field.name, k))))
            # opts.append(child(tds))
            opts.append(tds)

        if opts:
            opts[-1][0][0]['hideerror'] = False
        return parent(child(*opts), **attr)

