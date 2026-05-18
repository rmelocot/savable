import React, { useState, useEffect, useRef } from "react";
import { strictColors } from "./strictColorRules";

// ─── Subtle entry: each element fades + slides up with a staggered delay ───
const useEntryAnimation = () => {
  const [mounted, setMounted] = useState(false);
  useEffect(() => { requestAnimationFrame(() => setMounted(true)); }, []);
  const fadeUp = (delay = 0) => ({
    opacity: mounted ? 1 : 0,
    transform: mounted ? "translateY(0px)" : "translateY(12px)",
    transition: `opacity 0.45s cubic-bezier(0.22,1,0.36,1) ${delay}ms, transform 0.45s cubic-bezier(0.22,1,0.36,1) ${delay}ms`,
  });
  const fadeRight = (delay = 0) => ({
    opacity: mounted ? 1 : 0,
    transform: mounted ? "translateX(0px)" : "translateX(18px)",
    transition: `opacity 0.5s cubic-bezier(0.22,1,0.36,1) ${delay}ms, transform 0.5s cubic-bezier(0.22,1,0.36,1) ${delay}ms`,
  });
  return { fadeUp, fadeRight };
};

function AddToFolderModal({ isOpen, onClose, allFolders, currentCategories, onConfirm, theme }) {
  const [tempCategories, setTempCategories] = useState(currentCategories);
  useEffect(() => { if (isOpen) setTempCategories(currentCategories); }, [isOpen, currentCategories]);
  const toggle = (name) => setTempCategories(prev => prev.includes(name) ? prev.filter(c => c !== name) : [...prev, name]);
  if (!isOpen) return null;

  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 200, display: "flex", alignItems: "center", justifyContent: "center", background: theme.modalOverlay }}>
      <div style={{ background: theme.surface, borderRadius: "18px", padding: "24px", width: "100%", maxWidth: "380px", margin: "0 16px", border: `1px solid ${theme.border}`, transition: "background 0.25s" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <h3 style={{ fontFamily: "inherit", fontSize: "15px", fontWeight: "700", color: theme.text, margin: 0 }}>Add to collection</h3>
          <button onClick={onClose} style={{ background: theme.surfaceAlt, border: `1px solid ${theme.border}`, width: "28px", height: "28px", borderRadius: "50%", cursor: "pointer", color: theme.textSub, fontSize: "13px", display: "flex", alignItems: "center", justifyContent: "center" }}>✕</button>
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginBottom: "20px" }}>
          {allFolders.map(folder => {
            const isSelected = tempCategories.includes(folder.name);
            const color = strictColors[folder.name] || folder.color || "#4F46E5";
            return (
              <button key={folder.id} onClick={() => toggle(folder.name)}
                style={{ background: isSelected ? color : theme.surfaceAlt, color: isSelected ? "white" : theme.textMed, border: `1px solid ${isSelected ? "transparent" : theme.border}`, padding: "5px 13px", borderRadius: "20px", fontSize: "12px", fontWeight: "600", fontFamily: "inherit", cursor: "pointer", transition: "all 0.18s" }}>
                {folder.name}
              </button>
            );
          })}
        </div>
        <button onClick={() => { onConfirm(tempCategories); onClose(); }}
          style={{ width: "100%", background: theme.text, color: theme.bg, border: "none", padding: "11px", borderRadius: "10px", fontSize: "13px", fontWeight: "600", cursor: "pointer", fontFamily: "inherit" }}>
          Save
        </button>
      </div>
    </div>
  );
}

const STAR_PATH = "M12 2 L14.9 9.26 L22.54 9.26 L16.47 13.97 L18.63 21.27 L12 17 L5.37 21.27 L7.53 13.97 L1.46 9.26 L9.1 9.26 Z";

function StarSvg({ fill, size = 26, theme }) {
  const id = `half-clip-${Math.random().toString(36).slice(2)}`;
  const isHalf = fill === "half";
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" style={{ display: "block", overflow: "visible" }}>
      {isHalf && <defs><clipPath id={id}><rect x="0" y="0" width="12" height="24" /></clipPath></defs>}
      <path d={STAR_PATH} fill={theme.hover} />
      {fill === "full" && <path d={STAR_PATH} fill="#F59E0B" />}
      {fill === "half" && <path d={STAR_PATH} fill="#F59E0B" clipPath={`url(#${id})`} />}
    </svg>
  );
}

function HalfStarRating({ rating, onChange, theme }) {
  const [hovered, setHovered] = useState(null);
  const display = hovered !== null ? hovered : rating;
  const handleMouseMove = (e, starIndex) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setHovered(e.clientX - rect.left < rect.width / 2 ? starIndex - 0.5 : starIndex);
  };
  const handleClick = (e, starIndex) => {
    const rect = e.currentTarget.getBoundingClientRect();
    onChange(e.clientX - rect.left < rect.width / 2 ? starIndex - 0.5 : starIndex);
  };
  return (
    <div style={{ display: "flex", gap: "2px" }} onMouseLeave={() => setHovered(null)}>
      {[1, 2, 3, 4, 5].map(star => {
        const fill = display >= star ? "full" : display >= star - 0.5 ? "half" : "empty";
        return (
          <div key={star} onMouseMove={e => handleMouseMove(e, star)} onClick={e => handleClick(e, star)}
            style={{ cursor: "pointer", transition: "transform 0.15s" }}
            onMouseEnter={e => e.currentTarget.style.transform = "scale(1.1)"}
            onMouseLeave={e => e.currentTarget.style.transform = "scale(1)"}>
            <StarSvg fill={fill} size={26} theme={theme} />
          </div>
        );
      })}
    </div>
  );
}

function PhotoGallery({ photos, onPhotosChange, theme }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [animating, setAnimating] = useState(false);
  const [nextIndex, setNextIndex] = useState(null);
  const [slideDir, setSlideDir] = useState(null);
  const fileInputRef = useRef(null);

  const navigate = (dir) => {
    if (animating || photos.length < 2) return;
    const next = (currentIndex + dir + photos.length) % photos.length;
    setNextIndex(next); setSlideDir(dir); setAnimating(true);
    setTimeout(() => { setCurrentIndex(next); setNextIndex(null); setAnimating(false); setSlideDir(null); }, 320);
  };

  const handleFileChange = (e) => {
    const files = Array.from(e.target.files);
    files.forEach(file => {
      const reader = new FileReader();
      reader.onload = (ev) => {
        onPhotosChange(prev => { const updated = [...prev, ev.target.result]; setCurrentIndex(updated.length - 1); return updated; });
      };
      reader.readAsDataURL(file);
    });
    e.target.value = "";
  };

  const handleRemove = () => {
    onPhotosChange(prev => {
      const updated = prev.filter((_, i) => i !== currentIndex);
      setCurrentIndex(Math.max(0, currentIndex - 1));
      return updated;
    });
  };

  if (photos.length === 0) {
    return (
      <div onClick={() => fileInputRef.current.click()}
        style={{ border: `1.5px dashed ${theme.border}`, borderRadius: "10px", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: "6px", padding: "28px 20px", cursor: "pointer", background: theme.surfaceAlt, transition: "border-color 0.2s, background 0.2s" }}
        onMouseEnter={e => { e.currentTarget.style.borderColor = theme.text; e.currentTarget.style.background = theme.hover; }}
        onMouseLeave={e => { e.currentTarget.style.borderColor = theme.border; e.currentTarget.style.background = theme.surfaceAlt; }}>
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={theme.border} strokeWidth="1.8"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
        <p style={{ fontFamily: "inherit", fontSize: "12px", color: theme.textMuted, margin: 0, fontWeight: "600" }}>Click to add photos</p>
        <p style={{ fontFamily: "inherit", fontSize: "11px", color: theme.border, margin: 0 }}>JPG, PNG, WEBP</p>
        <input ref={fileInputRef} type="file" accept="image/*" multiple onChange={handleFileChange} style={{ display: "none" }} />
      </div>
    );
  }

  return (
    <div>
      <div style={{ position: "relative", borderRadius: "10px", overflow: "hidden", background: "#111", aspectRatio: "4/3" }}>
        <div style={{ position: "absolute", inset: 0, transform: animating ? `translateX(${slideDir * -100}%)` : "translateX(0%)", transition: animating ? "transform 0.32s cubic-bezier(0.4,0,0.2,1)" : "none" }}>
          <img src={photos[currentIndex]} alt="" style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }} />
        </div>
        {animating && nextIndex !== null && (
          <div style={{ position: "absolute", inset: 0, animation: `slideIn${slideDir > 0 ? "Right" : "Left"} 0.32s cubic-bezier(0.4,0,0.2,1) forwards` }}>
            <img src={photos[nextIndex]} alt="" style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }} />
          </div>
        )}
        {photos.length > 1 && (
          <>
            <button onClick={() => navigate(-1)} style={{ position: "absolute", left: "10px", top: "50%", transform: "translateY(-50%)", background: "rgba(255,255,255,0.9)", border: "none", borderRadius: "50%", width: "30px", height: "30px", display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", zIndex: 2 }}>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#111" strokeWidth="2.5"><polyline points="15 18 9 12 15 6"/></svg>
            </button>
            <button onClick={() => navigate(1)} style={{ position: "absolute", right: "10px", top: "50%", transform: "translateY(-50%)", background: "rgba(255,255,255,0.9)", border: "none", borderRadius: "50%", width: "30px", height: "30px", display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", zIndex: 2 }}>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#111" strokeWidth="2.5"><polyline points="9 18 15 12 9 6"/></svg>
            </button>
          </>
        )}
        <div style={{ position: "absolute", bottom: "10px", left: "50%", transform: "translateX(-50%)", display: "flex", gap: "4px", zIndex: 2 }}>
          {photos.map((_, i) => (
            <div key={i} onClick={() => { if (!animating) setCurrentIndex(i); }}
              style={{ width: i === currentIndex ? "16px" : "5px", height: "5px", borderRadius: "3px", background: i === currentIndex ? "white" : "rgba(255,255,255,0.45)", cursor: "pointer", transition: "all 0.2s" }} />
          ))}
        </div>
        <button onClick={handleRemove} style={{ position: "absolute", top: "10px", right: "10px", zIndex: 2, background: "rgba(0,0,0,0.5)", border: "none", borderRadius: "50%", width: "26px", height: "26px", display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer" }}>
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: "10px" }}>
        <p style={{ fontFamily: "inherit", fontSize: "11px", color: theme.textMuted, margin: 0, fontWeight: "500" }}>{currentIndex + 1} of {photos.length}</p>
        <button onClick={() => fileInputRef.current.click()} style={{ background: theme.surfaceAlt, border: `1px solid ${theme.border}`, color: theme.textMed, borderRadius: "8px", padding: "5px 11px", fontSize: "11px", fontWeight: "600", cursor: "pointer", fontFamily: "inherit", display: "flex", alignItems: "center", gap: "4px" }}>
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          Add more
        </button>
        <input ref={fileInputRef} type="file" accept="image/*" multiple onChange={handleFileChange} style={{ display: "none" }} />
      </div>
    </div>
  );
}

export default function PostDetail({ onBack, onViewOnMap, data, setData, allFolders, theme }) {
  const [isEditing, setIsEditing] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const { fadeUp, fadeRight } = useEntryAnimation();

  if (!data || !data.categories) {
    return (
      <div style={{ padding: "40px", textAlign: "center", fontFamily: "inherit" }}>
        <button onClick={onBack} style={{ color: theme.text, background: "none", border: "none", cursor: "pointer", fontWeight: "700" }}>← Back</button>
        <p style={{ color: theme.textMuted, marginTop: "12px" }}>Entry not found.</p>
      </div>
    );
  }

  const isFavourited = data.categories.includes("Favourites");
  const handleToggleFavourite = () => {
    setData({ ...data, categories: isFavourited ? data.categories.filter(c => c !== "Favourites") : [...data.categories, "Favourites"] });
  };

  const getCategoryColor = (catName) => strictColors[catName] || allFolders.find(f => f.name === catName)?.color || "#4F46E5";
  const isTikTok = !!(data.externalUrls?.tiktok?.includes("tiktok.com"));
  const isInstagram = !!(data.externalUrls?.insta?.includes("instagram.com"));
  const isDark = theme.bg === "#111111";
  const hasLocation = !!(data.latitude && data.longitude) || !!(data.address);

  const getEmbedUrl = () => {
    const tt = data.externalUrls?.tiktok;
    const ig = data.externalUrls?.insta;
    if (tt?.includes("tiktok.com")) { const id = tt.split("/video/")[1]?.split("?")[0]; return id ? `https://www.tiktok.com/embed/v2/${id}` : null; }
    if (ig?.includes("instagram.com")) { return `${ig.split("?")[0].replace(/\/$/, "")}/embed/`; }
    return null;
  };

  const embedUrl = getEmbedUrl();
  const embedHeight = isTikTok ? 580 : 820;
  const photos = data.photos || [];
  const handlePhotosChange = (updater) => {
    const updated = typeof updater === "function" ? updater(photos) : updater;
    setData({ ...data, photos: updated });
  };

  const sectionCard = {
    background: theme.surface,
    border: `1px solid ${theme.border}`,
    borderRadius: "12px",
    padding: "14px 16px",
    marginBottom: "10px",
    transition: "background 0.25s, border-color 0.25s",
  };

  const labelStyle = {
    fontFamily: "inherit", fontSize: "10px", fontWeight: "700", color: theme.textMuted,
    textTransform: "uppercase", letterSpacing: "0.08em", margin: "0 0 8px",
  };

  const inputStyle = () => ({
    width: "100%", fontFamily: "inherit", fontSize: "13px", color: theme.text,
    background: theme.inputBg, border: `1px solid ${theme.border}`,
    borderRadius: "8px", padding: "7px 10px", outline: "none", boxSizing: "border-box",
    transition: "border-color 0.15s",
  });

  return (
    <div style={{ minHeight: "100vh", background: theme.bg, fontFamily: "'DM Sans', -apple-system, sans-serif", transition: "background 0.25s" }}>
      <style>{`
        @keyframes slideInRight { from { transform: translateX(100%); } to { transform: translateX(0%); } }
        @keyframes slideInLeft  { from { transform: translateX(-100%); } to { transform: translateX(0%); } }
      `}</style>

      <main style={{ maxWidth: "1100px", margin: "0 auto", padding: "28px 24px 80px" }}>

        {/* Back button */}
        <div style={fadeUp(0)}>
          <button onClick={onBack} style={{ background: "none", border: "none", cursor: "pointer", display: "flex", alignItems: "center", gap: "4px", color: theme.textMuted, fontFamily: "inherit", fontSize: "11px", fontWeight: "700", marginBottom: "24px", padding: 0, textTransform: "uppercase", letterSpacing: "0.06em", transition: "color 0.15s" }}
            onMouseEnter={e => e.currentTarget.style.color = theme.text}
            onMouseLeave={e => e.currentTarget.style.color = theme.textMuted}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="15 18 9 12 15 6"/></svg>
            Back
          </button>
        </div>

        <div style={{ display: "flex", gap: "36px", alignItems: "flex-start" }}>

          {/* LEFT */}
          <div style={{ flex: 1, minWidth: 0 }}>

            {/* Tags */}
            <div style={{ display: "flex", flexWrap: "wrap", gap: "5px", marginBottom: "12px", alignItems: "center", ...fadeUp(60) }}>
              {data.categories.map(cat => (
                <span key={cat} style={{ background: getCategoryColor(cat), color: "white", padding: "4px 12px", borderRadius: "20px", fontSize: "11px", fontWeight: "700", fontFamily: "inherit" }}>{cat}</span>
              ))}
              {isEditing && (
                <button onClick={() => setShowModal(true)} style={{ background: theme.surface, color: theme.textSub, border: `1px dashed ${theme.border}`, padding: "4px 12px", borderRadius: "20px", fontSize: "11px", fontWeight: "600", fontFamily: "inherit", cursor: "pointer" }}>+ Folder</button>
              )}
            </div>

            {/* Title */}
            <div style={fadeUp(110)}>
              {isEditing ? (
                <input value={data.title} onChange={e => setData({ ...data, title: e.target.value })} placeholder="Enter title..."
                  style={{ width: "100%", fontFamily: "inherit", fontSize: "24px", fontWeight: "800", color: theme.text, background: theme.surface, border: `1px solid ${theme.text}`, borderRadius: "10px", padding: "10px 14px", marginBottom: "16px", outline: "none", boxSizing: "border-box", letterSpacing: "-0.4px" }} />
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
                  {data.title || <span style={{ color: theme.border }}>Untitled</span>}
                </h2>
              )}
            </div>

            {/* Toolbar */}
            <div style={{ display: "flex", gap: "6px", marginBottom: "18px", ...fadeUp(160) }}>
              <button onClick={() => setIsEditing(!isEditing)}
                style={{ display: "flex", alignItems: "center", gap: "5px", background: isEditing ? theme.text : theme.surface, color: isEditing ? theme.bg : theme.textMed, border: `1px solid ${theme.border}`, padding: "7px 13px", borderRadius: "9px", fontSize: "12px", fontWeight: "600", cursor: "pointer", fontFamily: "inherit", transition: "all 0.2s" }}>
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                {isEditing ? "Save" : "Edit"}
              </button>
              <button onClick={handleToggleFavourite}
                style={{ display: "flex", alignItems: "center", gap: "5px", background: isFavourited ? "#FFF1F2" : theme.surface, color: "#EF4444", border: "1px solid #FECACA", padding: "7px 13px", borderRadius: "9px", fontSize: "12px", fontWeight: "600", cursor: "pointer", fontFamily: "inherit", transition: "all 0.2s" }}>
                <svg width="12" height="12" viewBox="0 0 24 24" fill={isFavourited ? "#EF4444" : "none"} stroke="#EF4444" strokeWidth="2" style={{ transition: "fill 0.2s" }}>
                  <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
                </svg>
                {isFavourited ? "Unfavourite" : "Favourite"}
              </button>
            </div>

            <div style={{ height: "1px", background: theme.border, marginBottom: "14px", ...fadeUp(200) }} />

            {/* Location */}
            <div style={{ ...sectionCard, ...fadeUp(220) }}>
              <p style={labelStyle}>Location</p>

              {/* View on map button — only shows if there's an address or coordinates */}
              {hasLocation && (
                <button
                  onClick={() => onViewOnMap?.(data.id)}
                  style={{
                    background: "none", border: "none", cursor: "pointer",
                    color: theme.text, fontFamily: "inherit", fontSize: "12px",
                    fontWeight: "700", padding: 0, marginBottom: "6px",
                    display: "flex", alignItems: "center", gap: "5px",
                    textDecoration: "underline", textUnderlineOffset: "2px",
                    transition: "opacity 0.15s",
                  }}
                  onMouseEnter={e => e.currentTarget.style.opacity = "0.6"}
                  onMouseLeave={e => e.currentTarget.style.opacity = "1"}
                >
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>
                  </svg>
                  View on map →
                </button>
              )}

              {isEditing ? (
                <input value={data.address || ""} onChange={e => setData({ ...data, address: e.target.value })} placeholder="Enter address..."
                  style={inputStyle()} onFocus={e => e.target.style.borderColor = theme.text} onBlur={e => e.target.style.borderColor = theme.border} />
              ) : (
                <p style={{ fontFamily: "inherit", fontSize: "12px", color: theme.textSub, margin: 0 }}>{data.address || "No address recorded"}</p>
              )}
            </div>

            {/* Rating */}
            <div style={{ ...sectionCard, ...fadeUp(270) }}>
              <p style={labelStyle}>Rating</p>
              <HalfStarRating rating={data.rating || 0} onChange={val => setData({ ...data, rating: val })} theme={theme} />
            </div>

            {/* Photos */}
            <div style={{ ...sectionCard, ...fadeUp(310) }}>
              <p style={labelStyle}>Photos</p>
              <PhotoGallery photos={photos} onPhotosChange={handlePhotosChange} theme={theme} />
            </div>

            {/* Notes */}
            <div style={fadeUp(350)}>
              <p style={labelStyle}>Notes</p>
              <textarea placeholder="Write about your experience..." value={data.notes} onChange={e => setData({ ...data, notes: e.target.value })}
                style={{ width: "100%", minHeight: "110px", background: theme.surface, border: `1px solid ${theme.border}`, borderRadius: "12px", padding: "12px 14px", fontFamily: "inherit", fontSize: "13px", color: theme.text, lineHeight: 1.6, resize: "vertical", outline: "none", boxSizing: "border-box", transition: "border-color 0.15s, background 0.25s" }}
                onFocus={e => e.target.style.borderColor = theme.text} onBlur={e => e.target.style.borderColor = theme.border} />
            </div>
          </div>

          {/* RIGHT — embed */}
          <div style={{ width: "400px", flexShrink: 0, ...fadeRight(80) }}>
            <div style={{ background: theme.surface, borderRadius: "14px", overflow: "hidden", border: `1px solid ${theme.border}`, transition: "background 0.25s, border-color 0.25s" }}>
              <div style={{ padding: "12px 16px", borderBottom: `1px solid ${theme.border}`, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div>
                  <p style={{ fontFamily: "inherit", fontSize: "10px", fontWeight: "700", color: theme.textMuted, textTransform: "uppercase", letterSpacing: "0.08em", margin: 0 }}>Original Post</p>
                  <p style={{ fontFamily: "inherit", fontSize: "13px", fontWeight: "700", color: theme.text, margin: "2px 0 0" }}>
                    {isTikTok ? "TikTok" : isInstagram ? "Instagram" : "No link"}
                  </p>
                </div>
                <div style={{ width: "30px", height: "30px", borderRadius: "8px", background: isTikTok ? "#111" : isInstagram ? "linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888)" : theme.surfaceAlt, border: !isTikTok && !isInstagram ? `1px solid ${theme.border}` : "none", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  {isTikTok && <svg width="12" height="12" viewBox="0 0 24 24" fill="white"><path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-2.88 2.5 2.89 2.89 0 0 1-2.89-2.89 2.89 2.89 0 0 1 2.89-2.89c.28 0 .54.04.79.1V9.01a6.33 6.33 0 0 0-.79-.05 6.34 6.34 0 0 0-6.34 6.34 6.34 6.34 0 0 0 6.34 6.34 6.34 6.34 0 0 0 6.33-6.34V8.69a8.18 8.18 0 0 0 4.78 1.52V6.75a4.85 4.85 0 0 1-1.01-.06z"/></svg>}
                  {isInstagram && <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2"><rect x="2" y="2" width="20" height="20" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="white" stroke="none"/></svg>}
                </div>
              </div>
              <div style={{ position: "relative", background: "#000", height: `${embedHeight}px`, overflow: "hidden" }}>
                {embedUrl ? (
                  <iframe src={embedUrl} allowFullScreen scrolling="no" allow="autoplay; clipboard-write; encrypted-media; picture-in-picture"
                    style={{ border: "none", position: "absolute", top: 0, left: 0, width: "100%", height: isTikTok ? "739px" : "100%", display: "block", background: "#000", colorScheme: isDark ? "dark" : "light" }} />
                ) : (
                  <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: "8px" }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.2)" strokeWidth="1.5"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
                    <p style={{ fontFamily: "inherit", fontSize: "12px", color: "rgba(255,255,255,0.3)", margin: 0 }}>Add a link to preview</p>
                  </div>
                )}
              </div>
              <div style={{ padding: "11px 16px", background: theme.surfaceAlt, borderTop: `1px solid ${theme.border}`, display: "flex", alignItems: "center", justifyContent: "space-between", transition: "background 0.25s" }}>
                <p style={{ fontFamily: "inherit", fontSize: "11px", color: theme.textMuted, margin: 0, fontWeight: "500" }}>
                  {isTikTok ? "tiktok.com" : isInstagram ? "instagram.com" : "—"}
                </p>
                <a href={data.externalUrls?.tiktok || data.externalUrls?.insta || "#"} target="_blank" rel="noopener noreferrer"
                  style={{ background: theme.text, color: theme.bg, textDecoration: "none", padding: "6px 14px", borderRadius: "8px", fontSize: "12px", fontWeight: "700", fontFamily: "inherit", display: "flex", alignItems: "center", gap: "5px", transition: "all 0.25s" }}>
                  {isInstagram ? "View" : "Watch"}
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
                </a>
              </div>
            </div>
          </div>
        </div>
      </main>

      <AddToFolderModal isOpen={showModal} onClose={() => setShowModal(false)} allFolders={allFolders} currentCategories={data.categories} onConfirm={(newCats) => setData({ ...data, categories: newCats })} theme={theme} />
    </div>
  );
}
