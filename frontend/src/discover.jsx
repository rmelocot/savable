import React, { useState, useRef, useEffect } from "react";
import { strictColors } from "./strictColorRules";

const PLACEHOLDER_IMAGES = [
  "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=600&auto=format&fit=crop",
  "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=600&auto=format&fit=crop",
  "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=600&auto=format&fit=crop",
  "https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=600&auto=format&fit=crop",
];

const discoverThumbCache = {};

function useFolderThumbnail(folder, allPosts) {
  const firstPost = allPosts?.find(p => p.categories?.includes(folder.name));
  const tiktokUrl = firstPost?.externalUrls?.tiktok || "";
  const [thumb, setThumb] = useState(() => discoverThumbCache[tiktokUrl] || null);

  useEffect(() => {
    if (!tiktokUrl || !tiktokUrl.includes("tiktok.com")) return;
    if (discoverThumbCache[tiktokUrl]) { setThumb(discoverThumbCache[tiktokUrl]); return; }
    fetch(`https://www.tiktok.com/oembed?url=${encodeURIComponent(tiktokUrl)}`)
      .then(r => r.json())
      .then(data => {
        if (data.thumbnail_url) {
          discoverThumbCache[tiktokUrl] = data.thumbnail_url;
          setThumb(data.thumbnail_url);
        }
      })
      .catch(() => {});
  }, [tiktokUrl]);

  return thumb || folder.image || PLACEHOLDER_IMAGES[0];
}

function FolderCard({ folder, allPosts, onClick, isManageMode, isSelected, onToggleSelect, index, theme }) {
  const cardThumb = useFolderThumbnail(folder, allPosts);
  const isProtected = folder.protected;
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setMounted(true), index * 60);
    return () => clearTimeout(t);
  }, [index]);

  const handleClick = () => {
    if (isManageMode) {
      if (!isProtected) onToggleSelect(folder.id);
    } else {
      onClick();
    }
  };

  return (
    <div
      onClick={handleClick}
      style={{
        cursor: "pointer",
        opacity: mounted ? 1 : 0,
        transform: mounted ? "translateY(0)" : "translateY(18px)",
        transition: "opacity 0.5s ease, transform 0.5s ease",
      }}
    >
      <div
        style={{
          position: "relative",
          borderRadius: "14px",
          overflow: "hidden",
          aspectRatio: "3/4",
          border: isSelected ? "2px solid #EF4444" : `1px solid ${theme.border}`,
          transition: "border-color 0.15s, transform 0.15s",
          background: theme.cardBg,
        }}
        onMouseEnter={e => { e.currentTarget.style.transform = "translateY(-3px)"; }}
        onMouseLeave={e => { e.currentTarget.style.transform = "translateY(0)"; }}
      >
        <img
          src={cardThumb}
          alt={folder.name}
          style={{
            width: "100%", height: "100%", objectFit: "cover", display: "block",
            filter: isManageMode && isSelected ? "brightness(0.75)" : "none",
            transition: "filter 0.2s",
          }}
        />

        {/* Gradient overlay */}
        <div style={{ position: "absolute", inset: 0, background: "linear-gradient(to top, rgba(0,0,0,0.72) 0%, rgba(0,0,0,0.08) 55%, rgba(0,0,0,0) 100%)" }} />

        {/* Top-right indicator */}
        {!isManageMode && (
          folder.name === "Favourites" ? (
            <div style={{
              position: "absolute", top: "10px", right: "10px",
              background: "rgba(255,255,255,0.18)", backdropFilter: "blur(4px)",
              borderRadius: "50%", width: "26px", height: "26px",
              display: "flex", alignItems: "center", justifyContent: "center",
              border: "1px solid rgba(255,255,255,0.25)",
            }}>
              <svg width="11" height="11" viewBox="0 0 24 24" fill={folder.color || "#4F46E5"} stroke={folder.color || "#4F46E5"} strokeWidth="2">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
              </svg>
            </div>
          ) : (
            <div style={{
              position: "absolute", top: "10px", right: "10px",
              width: "8px", height: "8px", borderRadius: "50%",
              background: folder.color || "#4F46E5",
              boxShadow: "0 0 0 2px rgba(255,255,255,0.9)",
            }} />
          )
        )}

        {isManageMode && !isProtected && (
          <div style={{
            position: "absolute", top: "10px", right: "10px",
            width: "22px", height: "22px", borderRadius: "50%",
            background: isSelected ? "#EF4444" : "rgba(255,255,255,0.92)",
            border: isSelected ? "2px solid white" : "1.5px solid rgba(255,255,255,0.7)",
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>
            {isSelected && (
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            )}
          </div>
        )}

        {isManageMode && isProtected && (
          <div style={{
            position: "absolute", top: "10px", right: "10px",
            width: "22px", height: "22px", borderRadius: "50%",
            background: "rgba(255,255,255,0.92)",
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#9CA3AF" strokeWidth="2.5">
              <rect x="3" y="11" width="18" height="11" rx="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
          </div>
        )}

        {/* Bottom label */}
        <div style={{ position: "absolute", bottom: "14px", left: "14px", right: "14px" }}>
          <p style={{ fontFamily: "inherit", fontSize: "15px", fontWeight: "700", color: "white", margin: 0, letterSpacing: "-0.2px" }}>
            {folder.name}
          </p>
          <p style={{ fontFamily: "inherit", fontSize: "11px", color: "rgba(255,255,255,0.65)", margin: "2px 0 0", fontWeight: "400" }}>
            {isManageMode
              ? isProtected ? "Protected" : isSelected ? "Selected" : "Tap to select"
              : "View collection"}
          </p>
        </div>
      </div>
    </div>
  );
}

function Modal({ isOpen, onClose, children, theme }) {
  if (!isOpen) return null;
  return (
    <div
      style={{ position: "fixed", inset: 0, zIndex: 200, display: "flex", alignItems: "center", justifyContent: "center", background: theme.modalOverlay }}
      onClick={onClose}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{ background: theme.surface, borderRadius: "18px", padding: "24px", width: "100%", maxWidth: "400px", margin: "0 16px", border: `1px solid ${theme.border}`, transition: "background 0.25s" }}
      >
        {children}
      </div>
    </div>
  );
}

function DeleteFoldersModal({ isOpen, onClose, onConfirm, count, folderNames, theme }) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} theme={theme}>
      <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "16px" }}>
        <div style={{ width: "40px", height: "40px", borderRadius: "10px", background: "#FEF2F2", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, border: "1px solid #FECACA" }}>
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#EF4444" strokeWidth="2">
            <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
            <path d="M10 11v6M14 11v6"/><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
          </svg>
        </div>
        <div>
          <h3 style={{ fontFamily: "inherit", fontSize: "15px", fontWeight: "700", color: theme.text, margin: 0 }}>Delete {count} {count === 1 ? "folder" : "folders"}?</h3>
          <p style={{ fontFamily: "inherit", fontSize: "12px", color: theme.textMuted, margin: "2px 0 0" }}>This can't be undone</p>
        </div>
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "5px", marginBottom: "20px" }}>
        {folderNames.map(name => (
          <span key={name} style={{ background: "#FEF2F2", color: "#B91C1C", borderRadius: "6px", padding: "3px 10px", fontSize: "12px", fontWeight: "600", fontFamily: "inherit", border: "1px solid #FECACA" }}>{name}</span>
        ))}
      </div>
      <div style={{ display: "flex", gap: "8px" }}>
        <button onClick={onClose} style={{ flex: 1, background: theme.surfaceAlt, border: `1px solid ${theme.border}`, color: theme.textMed, padding: "10px", borderRadius: "10px", fontSize: "13px", fontWeight: "600", cursor: "pointer", fontFamily: "inherit" }}>Cancel</button>
        <button onClick={onConfirm} style={{ flex: 1, background: theme.text, border: "none", color: theme.bg, padding: "10px", borderRadius: "10px", fontSize: "13px", fontWeight: "600", cursor: "pointer", fontFamily: "inherit" }}>Delete</button>
      </div>
    </Modal>
  );
}

export default function Discover({ folders, onFolderClick, onAddFolder, allPosts, onDeleteFolders, theme }) {
  const [showModal, setShowModal] = useState(false);
  const [folderName, setFolderName] = useState("");
  const [folderColor, setFolderColor] = useState("#4F46E5");
  const colorInputRef = useRef(null);
  const [isManageMode, setIsManageMode] = useState(false);
  const [selectedFolderIds, setSelectedFolderIds] = useState([]);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const handleSave = () => {
    if (!folderName.trim()) return;
    onAddFolder({ name: folderName, color: folderColor, image: PLACEHOLDER_IMAGES[Math.floor(Math.random() * PLACEHOLDER_IMAGES.length)] });
    setFolderName(""); setFolderColor("#4F46E5"); setShowModal(false);
  };

  const toggleFolderSelect = (id) => setSelectedFolderIds(prev => prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]);
  const exitManageMode = () => { setIsManageMode(false); setSelectedFolderIds([]); };

  const handleDeleteConfirm = () => {
    const namesToDelete = folders.filter(f => selectedFolderIds.includes(f.id) && !f.protected).map(f => f.name);
    onDeleteFolders?.(namesToDelete);
    setShowDeleteConfirm(false);
    exitManageMode();
  };

  const selectedFolderNames = folders.filter(f => selectedFolderIds.includes(f.id) && !f.protected).map(f => f.name);

  const inputStyle = {
    width: "100%", background: theme.inputBg, border: `1px solid ${theme.border}`, borderRadius: "10px",
    padding: "9px 12px", fontSize: "14px", fontFamily: "inherit", color: theme.text, outline: "none",
    boxSizing: "border-box", transition: "border-color 0.15s",
  };

  return (
    <div style={{ minHeight: "100vh", background: theme.bg, transition: "background 0.25s" }}>
      <main style={{ maxWidth: "1200px", margin: "0 auto", padding: "32px 24px 80px" }}>

        {/* Header */}
        <div style={{ marginBottom: "28px", display: "flex", alignItems: "flex-end", justifyContent: "space-between" }}>
          <div>
            <p style={{ fontFamily: "inherit", fontSize: "11px", fontWeight: "600", color: theme.textMuted, margin: "0 0 4px", textTransform: "uppercase", letterSpacing: "0.08em" }}>Collections</p>
            <h2 style={{ fontFamily: "inherit", fontSize: "26px", fontWeight: "800", color: theme.text, margin: 0, letterSpacing: "-0.6px" }}>Discover</h2>
            {isManageMode && (
              <p style={{ fontFamily: "inherit", fontSize: "12px", color: theme.textMuted, margin: "4px 0 0" }}>
                {selectedFolderIds.length > 0
                  ? <span style={{ color: "#EF4444", fontWeight: "700" }}>{selectedFolderIds.length} selected</span>
                  : "Tap folders to select"}
              </p>
            )}
          </div>

          <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
            {isManageMode && selectedFolderIds.length > 0 && (
              <button
                onClick={() => setShowDeleteConfirm(true)}
                style={{ display: "flex", alignItems: "center", gap: "5px", background: theme.text, color: theme.bg, border: "none", padding: "8px 14px", borderRadius: "10px", fontSize: "13px", fontWeight: "600", cursor: "pointer", fontFamily: "inherit" }}
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6M14 11v6"/></svg>
                Delete {selectedFolderIds.length}
              </button>
            )}

            <button
              onClick={() => isManageMode ? exitManageMode() : setIsManageMode(true)}
              style={{ display: "flex", alignItems: "center", gap: "5px", background: isManageMode ? theme.text : theme.surface, color: isManageMode ? theme.bg : theme.textMed, border: `1px solid ${theme.border}`, padding: "8px 14px", borderRadius: "10px", fontSize: "13px", fontWeight: "600", cursor: "pointer", fontFamily: "inherit" }}
            >
              {isManageMode ? "Done" : (
                <>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                  Manage
                </>
              )}
            </button>

            {!isManageMode && (
              <button
                onClick={() => setShowModal(true)}
                style={{ display: "flex", alignItems: "center", gap: "5px", background: theme.text, color: theme.bg, border: "none", padding: "8px 14px", borderRadius: "10px", fontSize: "13px", fontWeight: "600", cursor: "pointer", fontFamily: "inherit" }}
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                New folder
              </button>
            )}
          </div>
        </div>

        {/* Grid */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(185px, 1fr))", gap: "14px" }}>
          {folders.map((folder, index) => (
            <FolderCard
              key={folder.id}
              folder={folder}
              allPosts={allPosts}
              onClick={() => onFolderClick(folder.name)}
              isManageMode={isManageMode}
              isSelected={selectedFolderIds.includes(folder.id)}
              onToggleSelect={toggleFolderSelect}
              index={index}
              theme={theme}
            />
          ))}
        </div>
      </main>

      {/* Create Folder Modal */}
      <Modal isOpen={showModal} onClose={() => setShowModal(false)} theme={theme}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
          <h3 style={{ fontFamily: "inherit", fontSize: "15px", fontWeight: "700", color: theme.text, margin: 0 }}>New folder</h3>
          <button onClick={() => setShowModal(false)} style={{ background: theme.surfaceAlt, border: `1px solid ${theme.border}`, width: "28px", height: "28px", borderRadius: "50%", cursor: "pointer", color: theme.textSub, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "13px" }}>✕</button>
        </div>

        <div style={{ marginBottom: "12px" }}>
          <label style={{ display: "block", fontFamily: "inherit", fontSize: "11px", fontWeight: "600", color: theme.textMuted, marginBottom: "6px", textTransform: "uppercase", letterSpacing: "0.06em" }}>Name</label>
          <input
            value={folderName}
            onChange={e => setFolderName(e.target.value)}
            placeholder="e.g. Hidden Gems"
            style={inputStyle}
            onFocus={e => e.target.style.borderColor = theme.text}
            onBlur={e => e.target.style.borderColor = theme.border}
          />
        </div>

        <div style={{ marginBottom: "20px" }}>
          <label style={{ display: "block", fontFamily: "inherit", fontSize: "11px", fontWeight: "600", color: theme.textMuted, marginBottom: "6px", textTransform: "uppercase", letterSpacing: "0.06em" }}>Color</label>
          <div
            onClick={() => colorInputRef.current.click()}
            style={{ background: theme.inputBg, border: `1px solid ${theme.border}`, borderRadius: "10px", padding: "9px 12px", display: "flex", alignItems: "center", justifyContent: "space-between", cursor: "pointer" }}
          >
            <span style={{ fontFamily: "inherit", fontSize: "13px", color: theme.textMed }}>{folderColor}</span>
            <div style={{ width: "20px", height: "20px", borderRadius: "50%", background: folderColor, border: "2px solid white", boxShadow: "0 0 0 1px #E8E8E6" }} />
          </div>
          <input ref={colorInputRef} type="color" value={folderColor} onChange={e => setFolderColor(e.target.value)} style={{ position: "absolute", opacity: 0, pointerEvents: "none" }} />
        </div>

        <div style={{ display: "flex", gap: "8px" }}>
          <button onClick={() => setShowModal(false)} style={{ flex: 1, background: theme.surfaceAlt, border: `1px solid ${theme.border}`, color: theme.textMed, padding: "10px", borderRadius: "10px", fontSize: "13px", fontWeight: "600", cursor: "pointer", fontFamily: "inherit" }}>Cancel</button>
          <button
            onClick={handleSave}
            disabled={!folderName.trim()}
            style={{ flex: 1, background: folderName.trim() ? theme.text : theme.border, border: "none", color: folderName.trim() ? theme.bg : theme.textMuted, padding: "10px", borderRadius: "10px", fontSize: "13px", fontWeight: "600", cursor: folderName.trim() ? "pointer" : "not-allowed", fontFamily: "inherit" }}
          >
            Create
          </button>
        </div>
      </Modal>

      <DeleteFoldersModal isOpen={showDeleteConfirm} onClose={() => setShowDeleteConfirm(false)} onConfirm={handleDeleteConfirm} count={selectedFolderIds.length} folderNames={selectedFolderNames} theme={theme} />
    </div>
  );
}
