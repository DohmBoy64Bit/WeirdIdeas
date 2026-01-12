from backend.app.services.category_service import create_category, import_images_from_dir, list_categories, get_category
import os


def test_create_and_list_categories(tmp_path):
    c = create_category('Nature', 'Nature images', difficulty=2)
    assert c['name'] == 'Nature'
    cats = list_categories()
    assert any(x['id'] == c['id'] for x in cats)


def test_import_images(tmp_path, monkeypatch):
    # create temporary image files
    d = tmp_path / 'imgs'
    d.mkdir()
    p1 = d / 'a.png'
    p1.write_bytes(b'PNG')
    p2 = d / 'b.jpg'
    p2.write_bytes(b'JPG')

    c = create_category('TestImport')
    added = import_images_from_dir(c['id'], str(d))
    assert added == 2
    c2 = get_category(c['id'])
    assert len(c2['images']) >= 2