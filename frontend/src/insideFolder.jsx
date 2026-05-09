import React, { useState, useRef, useEffect } from "react";
import { strictColors } from "./strictColorRules";

const thumbCache = {};

function useThumbnail(post) {
  const tiktok = post?.externalUrls?.tiktok || "";
  const insta = post?.externalUrls?.insta || "";
  const cacheKey = tiktok || insta;
  const [thumb, setThumb] = useState(() => thumbCache[cacheKey] || null);

  useEffect(() => {
    if (!cacheKey) return;
    if (thumbCache[cacheKey]) { setThumb(thumbCache[cacheKey]); return; }
    if (tiktok && tiktok.includes("tiktok.com")) {
      fetch(`https://www.tiktok.com/oembed?url=${encodeURIComponent(tiktok)}`)
        .then(r => r.json()).then(data => { if (data.thumbnail_url) { thumbCache[cacheKey] = data.thumbnail_url; setThumb(data.thumbnail_url); } }).catch(() => {});
    }
    if (insta && insta.includes("instagram.com")) {
      const cleanUrl = insta.split("?")[0].replace(/\/$/, "");
      fetch(`https://corsproxy.io/?${encodeURIComponent(`${cleanUrl}/embed/`)}`)
        .then(r => r.text()).then(html => {
          const match = html.match(/<meta[^>]+property=["']og:image["'][^>]+content=["']([^"']+)["']/i) || html.match(/<meta[^>]+content=["']([^"']+)["'][^>]+property=["']og:image["']/i);
          if (match?.[1]) { const url = match[1].replace(/&amp;/g, "&"); thumbCache[cacheKey] = url; setThumb(url); }
        }).catch(() => {});
    }
  }, [tiktok, insta, cacheKey]);

  return thumb;
}

function getPostPlatform(post) {
  if (post?.externalUrls?.tiktok) return "tiktok";
  if (post?.externalUrls?.insta) return "instagram";
  return null;
}

function Modal({ isOpen, onClose, children, maxWidth = "400px", theme }) {
  if (!isOpen) return null;
  return (
    <div
      style={{ position: "fixed", inset: 0, zIndex: 200, display: "flex", alignItems: "center", justifyContent: "center", background: theme.modalOverlay }}
      onClick={onClose}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{ background: theme.surface, borderRadius: "18px", padding: "24px", width: "100%", maxWidth, margin: "0 16px", border: `1px solid ${theme.border}`, transition: "background 0.25s" }}
      >
        {children}
      </div>
    </div>
  );
}

function ModalHeader({ title, onClose, theme }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
      <h3 style={{ fontFamily: "inherit", fontSize: "15px", fontWeight: "700", color: theme.text, margin: 0 }}>{title}</h3>
      <button onClick={onClose} style={{ background: theme.surfaceAlt, border: `1px solid ${theme.border}`, width: "28px", height: "28px", borderRadius: "50%", cursor: "pointer", color: theme.textSub, fontSize: "13px", display: "flex", alignItems: "center", justifyContent: "center" }}>✕</button>
    </div>
  );
}

function AddPostModal({ isOpen, onClose, onConfirm, theme }) {
  const [urls, setUrls] = useState({ tiktok: "", insta: "" });
  const hasTiktok = urls.tiktok.trim().length > 0;
  const hasInsta = urls.insta.trim().length > 0;

  const urlInputStyle = {
    flex: 1, background: "none", border: "none", outline: "none",
    fontSize: "13px", fontFamily: "inherit", color: theme.text,
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} theme={theme}>
      <ModalHeader title="Add post" onClose={onClose} theme={theme} />
      <p style={{ fontFamily: "inherit", fontSize: "12px", color: theme.textMuted, margin: "0 0 16px" }}>Paste a TikTok or Instagram link</p>

      <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginBottom: "20px" }}>
        <div style={{ border: `1px solid ${hasTiktok ? theme.text : theme.border}`, borderRadius: "10px", padding: "10px 12px", background: theme.inputBg, opacity: hasInsta ? 0.4 : 1, pointerEvents: hasInsta ? "none" : "auto", transition: "border-color 0.15s" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div style={{ width: "26px", height: "26px", background: "#111", borderRadius: "6px", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="white"><path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-2.88 2.5 2.89 2.89 0 0 1-2.89-2.89 2.89 2.89 0 0 1 2.89-2.89c.28 0 .54.04.79.1V9.01a6.33 6.33 0 0 0-.79-.05 6.34 6.34 0 0 0-6.34 6.34 6.34 6.34 0 0 0 6.34 6.34 6.34 6.34 0 0 0 6.33-6.34V8.69a8.18 8.18 0 0 0 4.78 1.52V6.75a4.85 4.85 0 0 1-1.01-.06z"/></svg>
            </div>
            <input type="text" placeholder="TikTok URL" value={urls.tiktok} onChange={e => setUrls({ ...urls, tiktok: e.target.value })} style={urlInputStyle} />
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <div style={{ flex: 1, height: "1px", background: theme.border }} />
          <span style={{ fontSize: "11px", fontFamily: "inherit", color: theme.textMuted, fontWeight: "500" }}>or</span>
          <div style={{ flex: 1, height: "1px", background: theme.border }} />
        </div>

        <div style={{ border: `1px solid ${hasInsta ? "#E1306C" : theme.border}`, borderRadius: "10px", padding: "10px 12px", background: theme.inputBg, opacity: hasTiktok ? 0.4 : 1, pointerEvents: hasTiktok ? "none" : "auto", transition: "border-color 0.15s" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div style={{ width: "26px", height: "26px", borderRadius: "6px", background: "linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2"><rect x="2" y="2" width="20" height="20" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="white" stroke="none"/></svg>
            </div>
            <input type="text" placeholder="Instagram URL" value={urls.insta} onChange={e => setUrls({ ...urls, insta: e.target.value })} style={urlInputStyle} />
          </div>
        </div>
      </div>

      <button
        onClick={() => { onConfirm(urls); onClose(); setUrls({ tiktok: "", insta: "" }); }}
        disabled={!hasTiktok && !hasInsta}
        style={{ width: "100%", background: (hasTiktok || hasInsta) ? theme.text : theme.border, color: (hasTiktok || hasInsta) ? theme.bg : theme.textMuted, border: "none", padding: "11px", borderRadius: "10px", fontSize: "13px", fontWeight: "600", cursor: (hasTiktok || hasInsta) ? "pointer" : "not-allowed", fontFamily: "inherit" }}
      >
        Add post
      </button>
    </Modal>
  );
}

function CreateFolderModal({ isOpen, onClose, onConfirm, theme }) {
  const [folderName, setFolderName] = useState("");
  const [folderColor, setFolderColor] = useState("#4F46E5");
  const colorInputRef = useRef(null);
  const PLACEHOLDER_IMAGES = ["https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=600&auto=format&fit=crop"];

  return (
    <Modal isOpen={isOpen} onClose={onClose} theme={theme}>
      <ModalHeader title="New folder" onClose={onClose} theme={theme} />
      <div style={{ marginBottom: "12px" }}>
        <label style={{ display: "block", fontFamily: "inherit", fontSize: "11px", fontWeight: "600", color: theme.textMuted, marginBottom: "6px", textTransform: "uppercase", letterSpacing: "0.06em" }}>Name</label>
        <input
          value={folderName}
          onChange={e => setFolderName(e.target.value)}
          placeholder="e.g. Hidden Gems"
          style={{ width: "100%", background: theme.inputBg, border: `1px solid ${theme.border}`, borderRadius: "10px", padding: "9px 12px", fontSize: "13px", fontFamily: "inherit", color: theme.text, outline: "none", boxSizing: "border-box" }}
          onFocus={e => e.target.style.borderColor = theme.text}
          onBlur={e => e.target.style.borderColor = theme.border}
        />
      </div>
      <div style={{ marginBottom: "20px" }}>
        <label style={{ display: "block", fontFamily: "inherit", fontSize: "11px", fontWeight: "600", color: theme.textMuted, marginBottom: "6px", textTransform: "uppercase", letterSpacing: "0.06em" }}>Color</label>
        <div onClick={() => colorInputRef.current.click()} style={{ background: theme.inputBg, border: `1px solid ${theme.border}`, borderRadius: "10px", padding: "9px 12px", display: "flex", alignItems: "center", justifyContent: "space-between", cursor: "pointer" }}>
          <span style={{ fontFamily: "inherit", fontSize: "13px", color: theme.textMed }}>{folderColor}</span>
          <div style={{ width: "20px", height: "20px", borderRadius: "50%", background: folderColor, border: "2px solid white", boxShadow: "0 0 0 1px #E8E8E6" }} />
        </div>
        <input ref={colorInputRef} type="color" value={folderColor} onChange={e => setFolderColor(e.target.value)} style={{ position: "absolute", opacity: 0, pointerEvents: "none" }} />
      </div>
      <div style={{ display: "flex", gap: "8px" }}>
        <button onClick={onClose} style={{ flex: 1, background: theme.surfaceAlt, border: `1px solid ${theme.border}`, color: theme.textMed, padding: "10px", borderRadius: "10px", fontSize: "13px", fontWeight: "600", cursor: "pointer", fontFamily: "inherit" }}>Cancel</button>
        <button
          onClick={() => { if (!folderName.trim()) return; onConfirm({ name: folderName, color: folderColor, image: PLACEHOLDER_IMAGES[0] }); setFolderName(""); setFolderColor("#4F46E5"); }}
          disabled={!folderName.trim()}
          style={{ flex: 1, background: folderName.trim() ? theme.text : theme.border, border: "none", color: folderName.trim() ? theme.bg : theme.textMuted, padding: "10px", borderRadius: "10px", fontSize: "13px", fontWeight: "600", cursor: folderName.trim() ? "pointer" : "not-allowed", fontFamily: "inherit" }}
        >
          Create
        </button>
      </div>
    </Modal>
  );
}

function FolderPickerModal({ isOpen, onClose, allFolders, currentFolderName, onConfirm, onCreateFolder, selectedPostIds, allPosts, actionType, theme }) {
  const [selected, setSelected] = useState([]);
  useEffect(() => { if (isOpen) setSelected([]); }, [isOpen]);

  const alreadyInFolder = (folderName) => {
    if (!selectedPostIds || !allPosts) return false;
    return selectedPostIds.every(id => allPosts.find(p => p.id === id)?.categories?.includes(folderName));
  };

  const toggle = (name) => { if (alreadyInFolder(name)) return; setSelected(prev => prev.includes(name) ? prev.filter(n => n !== name) : [...prev, name]); };
  const otherFolders = allFolders.filter(f => f.name !== currentFolderName);

  return (
    <Modal isOpen={isOpen} onClose={onClose} theme={theme}>
      <ModalHeader title={actionType === "move" ? "Move to" : "Copy to"} onClose={onClose} theme={theme} />
      <p style={{ fontFamily: "inherit", fontSize: "12px", color: theme.textMuted, margin: "0 0 14px" }}>Choose destination folders</p>

      <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginBottom: "10px" }}>
        {otherFolders.map(folder => {
          const isSel = selected.includes(folder.name);
          const isBlocked = alreadyInFolder(folder.name);
          return (
            <button
              key={folder.id}
              onClick={() => toggle(folder.name)}
              disabled={isBlocked}
              style={{
                background: isBlocked ? theme.surfaceAlt : isSel ? folder.color || theme.text : theme.surfaceAlt,
                color: isBlocked ? theme.border : isSel ? "white" : theme.textMed,
                border: `1px solid ${isBlocked ? theme.border : isSel ? "transparent" : theme.border}`,
                padding: "5px 13px", borderRadius: "20px", fontSize: "12px", fontWeight: "600",
                fontFamily: "inherit", cursor: isBlocked ? "not-allowed" : "pointer",
              }}
            >
              {folder.name}{isBlocked && " ✓"}
            </button>
          );
        })}
      </div>

      <button onClick={onCreateFolder} style={{ width: "100%", background: "none", border: `1px dashed ${theme.border}`, color: theme.textMuted, padding: "8px", borderRadius: "10px", fontSize: "12px", fontWeight: "600", fontFamily: "inherit", cursor: "pointer", marginBottom: "14px" }}>
        + New folder
      </button>

      <button
        onClick={() => { onConfirm(selected); onClose(); setSelected([]); }}
        disabled={selected.length === 0}
        style={{ width: "100%", background: selected.length > 0 ? theme.text : theme.border, color: selected.length > 0 ? theme.bg : theme.textMuted, border: "none", padding: "11px", borderRadius: "10px", fontSize: "13px", fontWeight: "600", cursor: selected.length > 0 ? "pointer" : "not-allowed", fontFamily: "inherit" }}
      >
        Confirm — {selected.length} folder{selected.length !== 1 ? "s" : ""}
      </button>
    </Modal>
  );
}

function SelectionActionModal({ isOpen, onClose, selectedCount, onAction, theme }) {
  const options = [
    { id: "move", label: "Move to folder", desc: "Remove from here, add to another", icon: <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg> },
    { id: "copy", label: "Copy to folder", desc: "Keep here, duplicate to another", icon: <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> },
    { id: "remove", label: "Remove from folder", desc: "Remove from this folder only", icon: <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/></svg> }
  ];

  return (
    <Modal isOpen={isOpen} onClose={onClose} theme={theme}>
      <ModalHeader title="Actions" onClose={onClose} theme={theme} />
      <p style={{ fontFamily: "inherit", fontSize: "12px", color: theme.textMuted, margin: "0 0 14px" }}>{selectedCount} post{selectedCount !== 1 ? "s" : ""} selected</p>
      <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
        {options.map(opt => (
          <button
            key={opt.id}
            onClick={() => { onClose(); onAction(opt.id); }}
            style={{ display: "flex", alignItems: "center", gap: "12px", background: theme.surfaceAlt, border: `1px solid ${theme.border}`, borderRadius: "10px", padding: "11px 14px", cursor: "pointer", textAlign: "left", width: "100%", transition: "background 0.12s" }}
            onMouseEnter={e => e.currentTarget.style.background = theme.hover}
            onMouseLeave={e => e.currentTarget.style.background = theme.surfaceAlt}
          >
            <div style={{ color: theme.textSub, flexShrink: 0 }}>{opt.icon}</div>
            <div style={{ flex: 1 }}>
              <p style={{ fontFamily: "inherit", fontSize: "13px", fontWeight: "600", color: theme.text, margin: 0 }}>{opt.label}</p>
              <p style={{ fontFamily: "inherit", fontSize: "11px", color: theme.textMuted, margin: "1px 0 0" }}>{opt.desc}</p>
            </div>
            <svg style={{ color: theme.border }} width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="9 18 15 12 9 6"/></svg>
          </button>
        ))}
      </div>
    </Modal>
  );
}

function PostCard({ post, index, isSelectMode, isSelected, onClick, theme }) {
  const thumb = useThumbnail(post);
  const platform = getPostPlatform(post);
  const isInstagram = platform === "instagram";
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setMounted(true), index * 60);
    return () => clearTimeout(t);
  }, [index]);

  return (
    <div
      onClick={onClick}
      style={{
        cursor: "pointer",
        opacity: mounted ? 1 : 0,
        transform: mounted ? "translateY(0)" : "translateY(18px)",
        transition: "opacity 0.5s ease, transform 0.5s ease",
      }}
    >
      <div
        style={{
          position: "relative", aspectRatio: "3/4", borderRadius: "12px", overflow: "hidden",
          background: theme.cardBg,
          border: isSelected ? `2px solid ${theme.text}` : `1px solid ${theme.border}`,
          transition: "transform 0.15s, border-color 0.15s",
        }}
        onMouseEnter={e => { e.currentTarget.style.transform = "translateY(-3px)"; }}
        onMouseLeave={e => { e.currentTarget.style.transform = "translateY(0)"; }}
      >
        {thumb && (
          <img src={thumb} alt={post.title || `Post ${index + 1}`} style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }} />
        )}

        {isInstagram && !thumb && (
          <div style={{ position: "absolute", inset: 0, background: "linear-gradient(135deg, #833ab4, #fd1d1d, #fcb045)", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: "6px" }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.8"><rect x="2" y="2" width="20" height="20" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1.2" fill="white" stroke="none"/></svg>
            <span style={{ fontFamily: "inherit", fontSize: "10px", fontWeight: "700", color: "rgba(255,255,255,0.9)" }}>Instagram</span>
          </div>
        )}

        {!isInstagram && !thumb && (
          <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={theme.border} strokeWidth="1.5"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
          </div>
        )}

        {isSelectMode && (
          <div style={{ position: "absolute", inset: 0, background: isSelected ? "rgba(0,0,0,0.2)" : "transparent", display: "flex", alignItems: "flex-end", justifyContent: "flex-end", padding: "8px" }}>
            <div style={{ width: "22px", height: "22px", borderRadius: "50%", background: isSelected ? theme.text : "rgba(255,255,255,0.9)", border: "2px solid white", display: "flex", alignItems: "center", justifyContent: "center" }}>
              {isSelected && <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke={theme.bg} strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg>}
            </div>
          </div>
        )}
      </div>

      <div style={{ marginTop: "8px" }}>
        <p style={{ fontFamily: "inherit", fontSize: "12px", fontWeight: "700", color: theme.text, margin: 0, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
          {post.title || "Untitled"}
        </p>
        {post.address && (
          <p style={{ fontFamily: "inherit", fontSize: "11px", color: theme.textMuted, margin: "2px 0 0", display: "flex", alignItems: "center", gap: "3px" }}>
            <svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
            {post.address.split(",")[0]}
          </p>
        )}
      </div>
    </div>
  );
}

export default function InsideFolder({ folderName, folderColor, onBack, onPostClick, onAddPost, posts, allFolders, allPosts, onUpdateFolder, onMovePosts, onCopyPosts, onRemovePosts, onAddFolder, onDeleteFolder, theme }) {
  const [isSelectMode, setIsSelectMode] = useState(false);
  const [selectedPosts, setSelectedPosts] = useState([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showActionModal, setShowActionModal] = useState(false);
  const [showFolderPicker, setShowFolderPicker] = useState(false);
  const [showCreateFolder, setShowCreateFolder] = useState(false);
  const [pendingAction, setPendingAction] = useState(null);

  const [isEditingName, setIsEditingName] = useState(false);
  const [editedName, setEditedName] = useState(folderName);
  const nameInputRef = useRef(null);
  const colorInputRef = useRef(null);

  const isProtected = allFolders?.find(f => f.name === folderName)?.protected;

  useEffect(() => { setEditedName(folderName); }, [folderName]);
  useEffect(() => { if (isEditingName) nameInputRef.current?.focus(); }, [isEditingName]);

  const commitNameEdit = () => {
    setIsEditingName(false);
    const trimmed = editedName.trim();
    if (trimmed && trimmed !== folderName) {
      onUpdateFolder?.(folderName, trimmed, folderColor);
    } else {
      setEditedName(folderName);
    }
  };

  const handleColorChange = (e) => {
    onUpdateFolder?.(folderName, folderName, e.target.value);
  };

  const toggleSelect = (id) => { if (!isSelectMode) return; setSelectedPosts(prev => prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]); };
  const exitSelectMode = () => { setIsSelectMode(false); setSelectedPosts([]); };

  const handleAction = (actionId) => {
    if (actionId === "remove") { onRemovePosts?.(selectedPosts); exitSelectMode(); }
    else { setPendingAction(actionId); setShowFolderPicker(true); }
  };

  const handleFolderPickerConfirm = (targetFolders) => {
    if (pendingAction === "move") onMovePosts?.(selectedPosts, targetFolders);
    else if (pendingAction === "copy") onCopyPosts?.(selectedPosts, targetFolders);
    exitSelectMode(); setPendingAction(null);
  };

  const handleCreateFolder = (folderData) => { onAddFolder?.(folderData); setShowCreateFolder(false); setShowFolderPicker(true); };

  const isFavourites = folderName === "Favourites";

  const btnSecondary = {
    display: "flex", alignItems: "center", gap: "5px", padding: "8px 14px",
    borderRadius: "10px", fontSize: "13px", fontWeight: "600", cursor: "pointer",
    fontFamily: "inherit", border: `1px solid ${theme.border}`, background: theme.surface, color: theme.textMed,
    transition: "all 0.2s",
  };

  return (
    <>
      <div style={{ minHeight: "100vh", background: theme.bg, transition: "background 0.25s" }}>
        <main style={{ maxWidth: "1200px", margin: "0 auto", padding: "28px 24px 80px" }}>

          <button onClick={onBack} style={{ background: "none", border: "none", cursor: "pointer", display: "flex", alignItems: "center", gap: "4px", color: theme.textMuted, fontFamily: "inherit", fontSize: "12px", fontWeight: "600", marginBottom: "20px", padding: 0, textTransform: "uppercase", letterSpacing: "0.05em" }}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="15 18 9 12 15 6"/></svg>
            Back
          </button>

          {/* Header */}
          <div style={{ marginBottom: "24px", display: "flex", alignItems: "flex-end", justifyContent: "space-between" }}>
            <div>
              <p style={{ fontFamily: "inherit", fontSize: "11px", fontWeight: "600", color: theme.textMuted, margin: "0 0 4px", textTransform: "uppercase", letterSpacing: "0.08em" }}>Collection</p>
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                {isFavourites ? (
                  <svg width="14" height="14" viewBox="0 0 24 24" fill={folderColor || "#4F46E5"} stroke={folderColor || "#4F46E5"} strokeWidth="2" style={{ flexShrink: 0 }}>
                    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
                  </svg>
                ) : (
                  <div
                    onClick={() => colorInputRef.current?.click()}
                    style={{ width: "13px", height: "13px", borderRadius: "50%", background: folderColor || "#4F46E5", flexShrink: 0, cursor: "pointer", border: "2px solid white", boxShadow: "0 0 0 1.5px rgba(0,0,0,0.12)", transition: "transform 0.15s" }}
                    onMouseEnter={e => e.currentTarget.style.transform = "scale(1.2)"}
                    onMouseLeave={e => e.currentTarget.style.transform = "scale(1)"}
                  />
                )}

                {!isFavourites && (
                  <input ref={colorInputRef} type="color" value={folderColor || "#4F46E5"} onChange={handleColorChange} style={{ position: "absolute", opacity: 0, pointerEvents: "none", width: 0, height: 0 }} />
                )}

                {isEditingName && !isProtected ? (
                  <input
                    ref={nameInputRef}
                    value={editedName}
                    onChange={e => setEditedName(e.target.value)}
                    onBlur={commitNameEdit}
                    onKeyDown={e => { if (e.key === "Enter") commitNameEdit(); if (e.key === "Escape") { setEditedName(folderName); setIsEditingName(false); } }}
                    style={{ fontFamily: "inherit", fontSize: "24px", fontWeight: "800", color: theme.text, background: theme.surface, border: `1px solid ${theme.text}`, borderRadius: "8px", padding: "2px 10px", outline: "none", letterSpacing: "-0.5px", maxWidth: "300px" }}
                  />
                ) : (
                  

                  <h2 style={{ 
                  fontFamily: "'GFS Didot', serif",
                  fontStyle: "normal",
                  fontSize: "40px", 
                  fontWeight: "400",        
                  color: theme.text, 
                  margin: "0 0 14px", 
                  letterSpacing: "0px",     
                  lineHeight: 1.2 
                }}>
                    {folderName}
                  </h2>
                )}

                {!isProtected && !isEditingName && (
                  <button
                    onClick={() => setIsEditingName(true)}
                    style={{ background: "none", border: "none", cursor: "pointer", color: theme.border, padding: "4px", display: "flex", alignItems: "center", borderRadius: "6px", transition: "color 0.12s, background 0.12s" }}
                    onMouseEnter={e => { e.currentTarget.style.color = theme.textMed; e.currentTarget.style.background = theme.hover; }}
                    onMouseLeave={e => { e.currentTarget.style.color = theme.border; e.currentTarget.style.background = "none"; }}
                  >
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                    </svg>
                  </button>
                )}
              </div>
              <p style={{ fontFamily: "inherit", fontSize: "12px", color: theme.textMuted, margin: "4px 0 0", fontWeight: "500" }}>
                {posts.length} {posts.length === 1 ? "post" : "posts"}
                {isSelectMode && selectedPosts.length > 0 && <span style={{ color: theme.text, fontWeight: "700" }}> · {selectedPosts.length} selected</span>}
              </p>
            </div>

            <div style={{ display: "flex", gap: "6px" }}>
              {isSelectMode && selectedPosts.length > 0 && (
                <button onClick={() => setShowActionModal(true)} style={{ ...btnSecondary, background: theme.text, color: theme.bg, border: "none" }}>
                  Actions <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="9 18 15 12 9 6"/></svg>
                </button>
              )}
              <button onClick={() => isSelectMode ? exitSelectMode() : setIsSelectMode(true)} style={{ ...btnSecondary, background: isSelectMode ? theme.text : theme.surface, color: isSelectMode ? theme.bg : theme.textMed, border: isSelectMode ? "none" : `1px solid ${theme.border}` }}>
                {isSelectMode ? "Done" : "Select"}
              </button>
              <button onClick={() => setShowAddModal(true)} style={{ ...btnSecondary, background: theme.text, color: theme.bg, border: "none" }}>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                Add post
              </button>
            </div>
          </div>

          {posts.length === 0 ? (
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "80px 0", textAlign: "center" }}>
              <div style={{ width: "52px", height: "52px", borderRadius: "14px", background: theme.surface, border: `1px solid ${theme.border}`, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: "12px" }}>
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={theme.border} strokeWidth="1.8"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
              </div>
              <p style={{ fontFamily: "inherit", fontSize: "14px", fontWeight: "700", color: theme.text, margin: "0 0 3px" }}>No posts yet</p>
              <p style={{ fontFamily: "inherit", fontSize: "12px", color: theme.textMuted, margin: "0 0 18px" }}>Add your first TikTok or Instagram post</p>
              <button onClick={() => setShowAddModal(true)} style={{ background: theme.text, color: theme.bg, border: "none", padding: "9px 20px", borderRadius: "10px", fontSize: "13px", fontWeight: "600", cursor: "pointer", fontFamily: "inherit" }}>Add first post</button>
            </div>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(155px, 1fr))", gap: "14px" }}>
              {posts.map((post, index) => (
                <PostCard
                  key={post.id}
                  post={post}
                  index={index}
                  isSelectMode={isSelectMode}
                  isSelected={selectedPosts.includes(post.id)}
                  onClick={() => isSelectMode ? toggleSelect(post.id) : onPostClick(post.id)}
                  theme={theme}
                />
              ))}
            </div>
          )}
        </main>
      </div>

      <AddPostModal isOpen={showAddModal} onClose={() => setShowAddModal(false)} onConfirm={onAddPost} theme={theme} />
      <SelectionActionModal isOpen={showActionModal} onClose={() => setShowActionModal(false)} selectedCount={selectedPosts.length} onAction={handleAction} theme={theme} />
      <FolderPickerModal isOpen={showFolderPicker} onClose={() => { setShowFolderPicker(false); setPendingAction(null); }} allFolders={allFolders || []} currentFolderName={folderName} onConfirm={handleFolderPickerConfirm} onCreateFolder={() => { setShowFolderPicker(false); setShowCreateFolder(true); }} selectedPostIds={selectedPosts} allPosts={allPosts || []} actionType={pendingAction} theme={theme} />
      <CreateFolderModal isOpen={showCreateFolder} onClose={() => { setShowCreateFolder(false); setShowFolderPicker(true); }} onConfirm={handleCreateFolder} theme={theme} />
    </>
  );
}
