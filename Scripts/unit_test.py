__author__ = 'HO.OPOYEN'

if not file_selector.selection:
    alert('Choose file first')
else:
    img_path = file_selector.selection[0]
    for tmpl in tmpls.templates:
        print 'Preparint template', tmpl
        pack = ImgPack(template = tmpls[tmpl], values ={'default.src': img_path})
        stack.append(pack)

    prepare_pdf(stack, 'unit_test.pdf')