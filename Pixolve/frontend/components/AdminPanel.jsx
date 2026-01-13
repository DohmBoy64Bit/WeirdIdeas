import React, {useState, useEffect} from 'react';

export default function AdminPanel({user, token}){
  const [categories, setCategories] = useState([]);
  const [newCategoryName, setNewCategoryName] = useState('');
  const [newCategoryDesc, setNewCategoryDesc] = useState('');
  const [newCategoryImages, setNewCategoryImages] = useState([]);
  const [editingCategory, setEditingCategory] = useState(null);
  const [editName, setEditName] = useState('');
  const [editDesc, setEditDesc] = useState('');
  const [editDifficulty, setEditDifficulty] = useState(1);
  const [editActive, setEditActive] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  useEffect(() => {
    loadCategories();
  }, []);

  async function loadCategories(){
    try {
      const res = await fetch('/categories/');
      if (res.ok) {
        const data = await res.json();
        setCategories(data);
      }
    } catch(e) {
      console.error('Failed to load categories:', e);
    }
  }

  async function createCategory(){
    if (!newCategoryName.trim()) {
      setError('Category name is required');
      return;
    }
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      // First create the category
      const res = await fetch('/categories/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          name: newCategoryName.trim(),
          description: newCategoryDesc.trim() || null,
          difficulty: 1,
          active: true
        })
      });
      if (res.ok) {
        const cat = await res.json();
        
        // Upload images if any were selected
        if (newCategoryImages.length > 0) {
          for (const file of newCategoryImages) {
            const formData = new FormData();
            formData.append('file', file);
            await fetch(`/categories/${cat.id}/upload`, {
              method: 'POST',
              body: formData
            });
          }
        }
        
        // Reload categories to get updated image list
        await loadCategories();
        setNewCategoryName('');
        setNewCategoryDesc('');
        setNewCategoryImages([]);
        setSuccess(`Category "${cat.name}" created successfully!`);
      } else {
        const err = await res.json();
        setError(err.detail || 'Failed to create category');
      }
    } catch(e) {
      setError('Network error: ' + e.message);
    } finally {
      setLoading(false);
    }
  }

  function startEdit(category){
    setEditingCategory(category.id);
    setEditName(category.name);
    setEditDesc(category.description || '');
    setEditDifficulty(category.difficulty || 1);
    setEditActive(category.active !== false);
  }

  function cancelEdit(){
    setEditingCategory(null);
    setEditName('');
    setEditDesc('');
    setEditDifficulty(1);
    setEditActive(true);
  }

  async function saveEdit(categoryId){
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await fetch(`/categories/${categoryId}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          name: editName.trim(),
          description: editDesc.trim() || null,
          difficulty: editDifficulty,
          active: editActive
        })
      });
      if (res.ok) {
        await loadCategories();
        setEditingCategory(null);
        setSuccess('Category updated successfully!');
      } else {
        const err = await res.json();
        setError(err.detail || 'Failed to update category');
      }
    } catch(e) {
      setError('Network error: ' + e.message);
    } finally {
      setLoading(false);
    }
  }

  async function uploadImageToCategory(categoryId, file){
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await fetch(`/categories/${categoryId}/upload`, {
        method: 'POST',
        body: formData
      });
      if (res.ok) {
        await loadCategories();
        return true;
      }
      return false;
    } catch(e) {
      return false;
    }
  }

  async function removeImageFromCategory(categoryId, imagePath, categoryName){
    if (!confirm(`Are you sure you want to delete this image from "${categoryName}"?`)) {
      return;
    }
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await fetch(`/categories/${categoryId}/images/${encodeURIComponent(imagePath)}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        await loadCategories();
        setSuccess('Image deleted successfully!');
      } else {
        const err = await res.json().catch(() => ({detail: `HTTP ${res.status}: ${res.statusText}`}));
        setError(err.detail || 'Failed to delete image');
      }
    } catch(e) {
      setError('Network error: ' + e.message);
    } finally {
      setLoading(false);
    }
  }

  async function deleteCategory(categoryId, categoryName){
    if (!confirm(`Are you sure you want to delete category "${categoryName}"? This cannot be undone.`)) {
      return;
    }
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await fetch(`/categories/${categoryId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      if (res.ok) {
        setCategories(categories.filter(c => c.id !== categoryId));
        setSuccess(`Category "${categoryName}" deleted successfully!`);
      } else {
        const err = await res.json().catch(() => ({detail: `HTTP ${res.status}: ${res.statusText}`}));
        setError(err.detail || 'Failed to delete category');
      }
    } catch(e) {
      setError('Network error: ' + e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="pixel-container" style={{maxWidth: '1000px', width: '100%', margin: '0 auto'}}>
      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px'}}>
        <h1 className="h1">Admin Panel</h1>
        <div className="px-small">{user?.username || 'Admin'}</div>
      </div>


      {/* Messages */}
      {error && (
        <div style={{padding: '12px', background: 'rgba(255,68,68,0.2)', border: '2px solid var(--retro-red)', marginBottom: '16px', color: '#ff8080'}}>
          {error}
        </div>
      )}
      {success && (
        <div style={{padding: '12px', background: 'rgba(0,255,65,0.2)', border: '2px solid var(--retro-green)', marginBottom: '16px', color: '#80ff80'}}>
          {success}
        </div>
      )}

      {/* Categories Management */}
      <div className="panel neon-panel">
          <h2 className="h2" style={{marginBottom: '20px'}}>Manage Categories</h2>

          {/* Create Category Form */}
          <div style={{marginBottom: '32px', padding: '16px', background: 'rgba(0,0,0,0.2)', border: '2px solid rgba(0,255,247,0.2)'}}>
            <h3 className="h2" style={{marginBottom: '16px', fontSize: '11px'}}>Create New Category</h3>
            <div style={{marginTop: '16px'}}>
              <label className="px-small" style={{display: 'block', marginBottom: '8px'}}>Category Name</label>
              <input
                type="text"
                value={newCategoryName}
                onChange={e => setNewCategoryName(e.target.value)}
                placeholder="Enter category name"
                style={{width: '100%', boxSizing: 'border-box'}}
              />
            </div>
            <div style={{marginTop: '16px'}}>
              <label className="px-small" style={{display: 'block', marginBottom: '8px'}}>Description (optional)</label>
              <input
                type="text"
                value={newCategoryDesc}
                onChange={e => setNewCategoryDesc(e.target.value)}
                placeholder="Enter description"
                style={{width: '100%', boxSizing: 'border-box'}}
              />
            </div>
            <div style={{marginTop: '16px'}}>
              <label className="px-small" style={{display: 'block', marginBottom: '8px'}}>Images (optional)</label>
              <input
                type="file"
                multiple
                accept="image/png,image/jpeg,image/jpg"
                onChange={e => setNewCategoryImages(Array.from(e.target.files))}
                style={{width: '100%', boxSizing: 'border-box'}}
              />
              {newCategoryImages.length > 0 && (
                <div className="small-muted" style={{marginTop: '8px'}}>
                  {newCategoryImages.length} image(s) selected
                </div>
              )}
            </div>
            <div style={{marginTop: '20px'}}>
              <button className="btn btn-create" onClick={createCategory} disabled={loading}>
                {loading ? 'Creating...' : 'Create Category'}
              </button>
            </div>
          </div>

          {/* Categories List */}
          <div>
            <h3 className="h2" style={{marginBottom: '16px', fontSize: '11px'}}>Existing Categories</h3>
            {categories.length === 0 ? (
              <div className="small-muted">No categories found</div>
            ) : (
              <div style={{display: 'flex', flexDirection: 'column', gap: '12px'}}>
                {categories.map(cat => (
                  <div
                    key={cat.id}
                    style={{
                      padding: '16px',
                      background: 'rgba(0,0,0,0.2)',
                      border: '2px solid rgba(0,255,247,0.15)'
                    }}
                  >
                    {editingCategory === cat.id ? (
                      <div>
                        <div style={{marginBottom: '16px'}}>
                          <label className="px-small" style={{display: 'block', marginBottom: '8px'}}>Name</label>
                          <input
                            type="text"
                            value={editName}
                            onChange={e => setEditName(e.target.value)}
                            style={{width: '100%', boxSizing: 'border-box'}}
                          />
                        </div>
                        <div style={{marginBottom: '16px'}}>
                          <label className="px-small" style={{display: 'block', marginBottom: '8px'}}>Description</label>
                          <input
                            type="text"
                            value={editDesc}
                            onChange={e => setEditDesc(e.target.value)}
                            style={{width: '100%', boxSizing: 'border-box'}}
                          />
                        </div>
                        <div style={{marginBottom: '16px', display: 'flex', gap: '16px', alignItems: 'center'}}>
                          <div>
                            <label className="px-small" style={{display: 'block', marginBottom: '8px'}}>Difficulty</label>
                            <input
                              type="number"
                              value={editDifficulty}
                              onChange={e => setEditDifficulty(Number(e.target.value))}
                              min="1"
                              max="5"
                              style={{width: '80px', boxSizing: 'border-box'}}
                            />
                          </div>
                          <div>
                            <label className="px-small" style={{display: 'block', marginBottom: '8px'}}>Active</label>
                            <input
                              type="checkbox"
                              checked={editActive}
                              onChange={e => setEditActive(e.target.checked)}
                              style={{width: '20px', height: '20px'}}
                            />
                          </div>
                        </div>
                        <div style={{marginBottom: '16px'}}>
                          <label className="px-small" style={{display: 'block', marginBottom: '8px'}}>Add Images</label>
                          <input
                            type="file"
                            multiple
                            accept="image/png,image/jpeg,image/jpg"
                            onChange={async (e) => {
                              const files = Array.from(e.target.files);
                              for (const file of files) {
                                await uploadImageToCategory(cat.id, file);
                              }
                            }}
                            style={{width: '100%', boxSizing: 'border-box'}}
                          />
                        </div>
                        {cat.images && cat.images.length > 0 && (
                          <div style={{marginBottom: '16px'}}>
                            <div className="px-small" style={{marginBottom: '8px'}}>Current Images ({cat.images.length})</div>
                            <div style={{display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '8px'}}>
                              {cat.images.map((img, idx) => (
                                <div key={idx} style={{
                                  display: 'flex',
                                  justifyContent: 'space-between',
                                  alignItems: 'center',
                                  padding: '8px',
                                  background: 'rgba(0,0,0,0.2)',
                                  border: '1px solid rgba(0,255,247,0.1)'
                                }}>
                                  <div className="small-muted" style={{fontSize: '9px', wordBreak: 'break-all', flex: 1}}>
                                    {img}
                                  </div>
                                  <button
                                    className="btn btn-leave"
                                    onClick={() => removeImageFromCategory(cat.id, img, cat.name)}
                                    disabled={loading}
                                    style={{padding: '4px 8px', fontSize: '8px', marginLeft: '8px'}}
                                  >
                                    Delete
                                  </button>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                        <div style={{display: 'flex', gap: '12px'}}>
                          <button className="btn btn-ready" onClick={() => saveEdit(cat.id)} disabled={loading}>
                            {loading ? 'Saving...' : 'Save'}
                          </button>
                          <button className="btn btn-leave" onClick={cancelEdit} disabled={loading}>
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                        <div style={{flex: 1}}>
                          <div className="px-small" style={{fontWeight: 'bold'}}>{cat.name}</div>
                          {cat.description && (
                            <div className="small-muted" style={{marginTop: '4px'}}>{cat.description}</div>
                          )}
                          <div className="small-muted" style={{marginTop: '4px'}}>
                            Images: {cat.images?.length || 0} • Difficulty: {cat.difficulty || 1} • {cat.active ? 'Active' : 'Inactive'}
                          </div>
                        </div>
                        <div style={{display: 'flex', gap: '8px'}}>
                          <button
                            className="btn btn-ready"
                            onClick={() => startEdit(cat)}
                            disabled={loading}
                          >
                            Edit
                          </button>
                          <button
                            className="btn btn-leave"
                            onClick={() => deleteCategory(cat.id, cat.name)}
                            disabled={loading}
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
    </div>
  );
}
