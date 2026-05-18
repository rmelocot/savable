import React, { useState, useEffect, useRef } from "react";
import { strictColors } from "./strictColorRules";

function MapPinIcon(color) {
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="32" height="40" viewBox="0 0 32 40">
      <filter id="s" x="-50%" y="-50%" width="200%" height="200%">
        <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="rgba(0,0,0,0.25)"/>
      </filter>
      <ellipse cx="16" cy="37" rx="5" ry="3" fill="rgba(0,0,0,0.15)"/>
      <path d="M16 2C9.37 2 4 7.37 4 14c0 9 12 24 12 24S28 23 28 14C28 7.37 22.63 2 16 2z" fill="${color}" filter="url(#s)"/>
      <circle cx="16" cy="14" r="5" fill="white" opacity="0.9"/>
    </svg>
  `;
  return `data:image/svg+xml;base64,${btoa(svg)}`;
}

export default function Map({ posts, allFolders, theme, onPostClick }) {
  const [search, setSearch] = useState("");
  const [locationSearch, setLocationSearch] = useState("");
  const [activeCategory, setActiveCategory] = useState("All");
  const [hoveredPost, setHoveredPost] = useState(null);
  const [mounted, setMounted] = useState(false);
  const catScrollRef = useRef(null);
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersRef = useRef([]);

  useEffect(() => {
    const t = setTimeout(() => setMounted(true), 50);
    return () => clearTimeout(t);
  }, []);

  const dynamicCategories = ["All", ...(allFolders || []).map(f => f.name)];

  useEffect(() => {
    if (!dynamicCategories.includes(activeCategory)) {
      setActiveCategory("All");
    }
  }, [allFolders]);

  const getCategoryColor = (cat) => {
    if (cat === "All") return theme.text;
    return allFolders?.find(f => f.name === cat)?.color || strictColors[cat] || "#4F46E5";
  };

  // Posts that have coordinates
  const mappablePosts = (posts || []).filter(p => p.latitude && p.longitude);

  const filteredPosts = mappablePosts.filter(p => {
    const matchCat = activeCategory === "All" || p.categories?.includes(activeCategory);
    const matchSearch = !search || p.title?.toLowerCase().includes(search.toLowerCase()) || p.address?.toLowerCase().includes(search.toLowerCase());
    const matchLoc = !locationSearch || p.address?.toLowerCase().includes(locationSearch.toLowerCase());
    return matchCat && matchSearch && matchLoc;
  });

  // Load Leaflet
  const [leafletReady, setLeafletReady] = useState(false);
  useEffect(() => {
    if (window.L) { setLeafletReady(true); return; }
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
    document.head.appendChild(link);
    const script = document.createElement("script");
    script.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
    script.onload = () => setLeafletReady(true);
    document.head.appendChild(script);
  }, []);

  // Init map
  useEffect(() => {
    if (!leafletReady || !mapRef.current || mapInstanceRef.current) return;
    const L = window.L;
    const map = L.map(mapRef.current, {
      center: [43.6532, -79.3832],
      zoom: 11,
      zoomControl: false,
    });
    L.tileLayer(
      theme.bg === "#111111"
        ? "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        : "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
      { attribution: "", subdomains: "abcd", maxZoom: 19 }
    ).addTo(map);
    L.control.zoom({ position: "bottomright" }).addTo(map);
    mapInstanceRef.current = map;
  }, [leafletReady]);

  // Update markers — uses folder color for new folders automatically
  useEffect(() => {
    if (!mapInstanceRef.current || !window.L) return;
    const L = window.L;
    const map = mapInstanceRef.current;

    markersRef.current.forEach(m => m.remove());
    markersRef.current = [];

    filteredPosts.forEach(post => {
      const primaryCat = post.categories?.[0];
      const catColor = primaryCat
        ? (allFolders?.find(f => f.name === primaryCat)?.color || strictColors[primaryCat] || "#111")
        : "#111";

      const icon = L.icon({
        iconUrl: MapPinIcon(hoveredPost === post.id ? "#111" : catColor),
        iconSize: [32, 40],
        iconAnchor: [16, 40],
        popupAnchor: [0, -42],
      });

      const marker = L.marker([post.latitude, post.longitude], { icon })
        .addTo(map)
        .bindPopup(`
          <div style="font-family:'DM Sans',sans-serif;padding:2px 0;min-width:140px">
            <p style="margin:0 0 2px;font-weight:700;font-size:13px;color:#111">${post.title || "Untitled"}</p>
            <p style="margin:0;font-size:11px;color:#6B7280">${post.address?.split(",")[0] || ""}</p>
          </div>
        `, { maxWidth: 200 });

      markersRef.current.push(marker);
    });
  }, [filteredPosts, hoveredPost, allFolders]);

  // Fly to hovered post
  useEffect(() => {
    if (!mapInstanceRef.current || !hoveredPost) return;
    const post = filteredPosts.find(p => p.id === hoveredPost);
    if (post?.latitude && post?.longitude) {
      mapInstanceRef.current.flyTo([post.latitude, post.longitude], 14, { duration: 0.8 });
    }
  }, [hoveredPost]);

  const inputBase = {
    background: theme.inputBg,
    border: `1px solid ${theme.border}`,
    borderRadius: "10px",
    padding: "9px 12px 9px 34px",
    fontSize: "13px",
    fontFamily: "inherit",
    color: theme.text,
    outline: "none",
    width: "100%",
    boxSizing: "border-box",
    transition: "border-color 0.15s",
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: theme.bg,
      fontFamily: "'DM Sans', -apple-system, sans-serif",
      opacity: mounted ? 1 : 0,
      transform: mounted ? "translateY(0)" : "translateY(10px)",
      transition: "opacity 0.4s ease, transform 0.4s ease, background 0.25s",
    }}>
      <style>{`
        .leaflet-popup-content-wrapper {
          border-radius: 10px !important;
          box-shadow: 0 4px 20px rgba(0,0,0,0.12) !important;
          border: 1px solid #E8E8E6 !important;
        }
        .leaflet-popup-tip { display: none !important; }
        .leaflet-control-zoom {
          border: 1px solid ${theme.border} !important;
          border-radius: 10px !important;
          overflow: hidden;
          box-shadow: none !important;
        }
        .leaflet-control-zoom a {
          background: ${theme.surface} !important;
          color: ${theme.text} !important;
          border-bottom: 1px solid ${theme.border} !important;
          width: 30px !important;
          height: 30px !important;
          line-height: 30px !important;
          font-size: 16px !important;
        }
        .leaflet-control-zoom a:hover { background: ${theme.hover} !important; }
        .leaflet-control-attribution { display: none !important; }
        .cat-pill::-webkit-scrollbar { display: none; }
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>

      <main style={{ maxWidth: "1400px", margin: "0 auto", padding: "28px 24px 0" }}>

        {/* Header */}
        <div style={{ marginBottom: "20px" }}>
          <p style={{ fontFamily: "inherit", fontSize: "11px", fontWeight: "600", color: theme.textMuted, margin: "0 0 4px", textTransform: "uppercase", letterSpacing: "0.08em" }}>
            Explore
          </p>
          <h2 style={{
            fontFamily: "'GFS Didot', serif",
            fontSize: "40px",
            fontWeight: "400",
            color: theme.text,
            margin: "0 0 16px",
            letterSpacing: "0px",
            lineHeight: 1.2,
          }}>
            Explore
          </h2>

          {/* Search row */}
          <div style={{ display: "flex", gap: "10px", marginBottom: "14px" }}>
            <div style={{ position: "relative", flex: 1 }}>
              <svg style={{ position: "absolute", left: "11px", top: "50%", transform: "translateY(-50%)", pointerEvents: "none" }} width="13" height="13" viewBox="0 0 24 24" fill="none" stroke={theme.textMuted} strokeWidth="2.2">
                <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
              </svg>
              <input
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Search by name"
                style={inputBase}
                onFocus={e => e.target.style.borderColor = theme.text}
                onBlur={e => e.target.style.borderColor = theme.border}
              />
            </div>
            <div style={{ position: "relative", flex: 1 }}>
              <svg style={{ position: "absolute", left: "11px", top: "50%", transform: "translateY(-50%)", pointerEvents: "none" }} width="13" height="13" viewBox="0 0 24 24" fill="none" stroke={theme.textMuted} strokeWidth="2.2">
                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>
              </svg>
              <input
                value={locationSearch}
                onChange={e => setLocationSearch(e.target.value)}
                placeholder="Search by location"
                style={inputBase}
                onFocus={e => e.target.style.borderColor = theme.text}
                onBlur={e => e.target.style.borderColor = theme.border}
              />
            </div>
          </div>

          {/* Category pills — dynamic from allFolders */}
          <div
            ref={catScrollRef}
            className="cat-pill"
            style={{
              display: "flex",
              gap: "7px",
              overflowX: "auto",
              paddingBottom: "4px",
              scrollbarWidth: "none",
              msOverflowStyle: "none",
            }}
          >
            {dynamicCategories.map(cat => {
              const isActive = activeCategory === cat;
              const color = getCategoryColor(cat);
              // For light text detection: use white text on dark colors, dark text on light ones
              const isLight = color === "#e6ce00" || color === "#FFFF00"; // yellow-ish colors
              return (
                <button
                  key={cat}
                  onClick={() => setActiveCategory(cat)}
                  style={{
                    flexShrink: 0,
                    background: isActive ? color : theme.surface,
                    color: isActive ? (isLight ? "#111" : "white") : theme.textMed,
                    border: `1px solid ${isActive ? "transparent" : theme.border}`,
                    padding: "7px 16px",
                    borderRadius: "20px",
                    fontSize: "12px",
                    fontWeight: "700",
                    fontFamily: "inherit",
                    cursor: "pointer",
                    transition: "all 0.15s",
                    whiteSpace: "nowrap",
                  }}
                  onMouseEnter={e => { if (!isActive) { e.currentTarget.style.background = theme.hover; e.currentTarget.style.color = theme.text; } }}
                  onMouseLeave={e => { if (!isActive) { e.currentTarget.style.background = theme.surface; e.currentTarget.style.color = theme.textMed; } }}
                >
                  {cat}
                </button>
              );
            })}
          </div>
        </div>

        {/* Main layout: list + map */}
        <div style={{ display: "flex", gap: "0", height: "calc(100vh - 260px)", minHeight: "500px" }}>

          {/* Left: places list */}
          <div style={{
            width: "300px",
            flexShrink: 0,
            overflowY: "auto",
            paddingRight: "14px",
            scrollbarWidth: "thin",
            scrollbarColor: `${theme.border} transparent`,
          }}>
            {filteredPosts.length === 0 ? (
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "60px 0", textAlign: "center" }}>
                <div style={{ width: "46px", height: "46px", borderRadius: "12px", background: theme.surface, border: `1px solid ${theme.border}`, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: "10px" }}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={theme.border} strokeWidth="1.8">
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>
                  </svg>
                </div>
                <p style={{ fontFamily: "inherit", fontSize: "13px", fontWeight: "700", color: theme.text, margin: "0 0 3px" }}>No places found</p>
                <p style={{ fontFamily: "inherit", fontSize: "11px", color: theme.textMuted, margin: 0 }}>
                  {mappablePosts.length === 0 ? "Save posts to see them here" : "Try a different filter"}
                </p>
              </div>
            ) : (
              filteredPosts.map((post, i) => {
                const primaryCat = post.categories?.[0];
                const catColor = primaryCat
                  ? (allFolders?.find(f => f.name === primaryCat)?.color || strictColors[primaryCat] || "#4F46E5")
                  : "#4F46E5";
                const isHovered = hoveredPost === post.id;

                return (
                  <div
                    key={post.id}
                    onMouseEnter={() => setHoveredPost(post.id)}
                    onMouseLeave={() => setHoveredPost(null)}
                    onClick={() => onPostClick?.(post.id)}
                    style={{
                      background: isHovered ? theme.hover : theme.surface,
                      border: `1px solid ${isHovered ? theme.text : theme.border}`,
                      borderRadius: "12px",
                      padding: "12px 14px",
                      marginBottom: "8px",
                      cursor: "pointer",
                      opacity: mounted ? 1 : 0,
                      transform: mounted ? "translateY(0)" : "translateY(10px)",
                      transition: `opacity 0.4s ease ${i * 40}ms, transform 0.4s ease ${i * 40}ms, background 0.15s, border-color 0.15s`,
                    }}
                  >
                    {/* Title + favourite */}
                    <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "8px", marginBottom: "5px" }}>
                      <p style={{
                        fontFamily: "inherit", fontSize: "13px", fontWeight: "700",
                        color: theme.text, margin: 0,
                        whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
                        flex: 1,
                      }}>
                        {post.title || "Untitled"}
                      </p>
                      {post.categories?.includes("Favourites") && (
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="#eb008b" stroke="#eb008b" strokeWidth="2" style={{ flexShrink: 0, marginTop: "2px" }}>
                          <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
                        </svg>
                      )}
                    </div>

                    {/* Rating stars */}
                    {post.rating > 0 && (
                      <div style={{ display: "flex", alignItems: "center", gap: "2px", marginBottom: "6px" }}>
                        {[1, 2, 3, 4, 5].map(s => (
                          <svg key={s} width="10" height="10" viewBox="0 0 24 24">
                            <path d="M12 2 L14.9 9.26 L22.54 9.26 L16.47 13.97 L18.63 21.27 L12 17 L5.37 21.27 L7.53 13.97 L1.46 9.26 L9.1 9.26 Z"
                              fill={post.rating >= s ? "#F59E0B" : theme.border}
                              opacity={post.rating >= s - 0.5 && post.rating < s ? 0.5 : 1}
                            />
                          </svg>
                        ))}
                        <span style={{ fontFamily: "inherit", fontSize: "10px", color: theme.textMuted, marginLeft: "3px", fontWeight: "600" }}>
                          {post.rating} <span style={{ fontWeight: "400" }}>(Your Rating)</span>
                        </span>
                      </div>
                    )}

                    {/* Address */}
                    {post.address && (
                      <p style={{ fontFamily: "inherit", fontSize: "11px", color: theme.textMuted, margin: "0 0 8px", display: "flex", alignItems: "flex-start", gap: "4px", lineHeight: 1.4 }}>
                        <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginTop: "2px", flexShrink: 0 }}>
                          <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>
                        </svg>
                        {post.address}
                      </p>
                    )}

                    {/* Category tags — use folder color for each category */}
                    <div style={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
                      {post.categories?.filter(c => c !== "Favourites").map(cat => {
                        const tagColor = allFolders?.find(f => f.name === cat)?.color || strictColors[cat] || "#4F46E5";
                        const tagLight = tagColor === "#e6ce00" || tagColor === "#FFFF00";
                        return (
                          <span key={cat} style={{
                            background: tagColor,
                            color: tagLight ? "#111" : "white",
                            padding: "2px 8px", borderRadius: "20px",
                            fontSize: "10px", fontWeight: "700", fontFamily: "inherit",
                          }}>
                            {cat}
                          </span>
                        );
                      })}
                    </div>

                    {/* Visit post link */}
                    <button
                      onClick={e => { e.stopPropagation(); onPostClick?.(post.id); }}
                      style={{
                        background: "none", border: "none", cursor: "pointer",
                        color: theme.textMuted, fontFamily: "inherit", fontSize: "11px",
                        fontWeight: "600", padding: "6px 0 0",
                        display: "flex", alignItems: "center", gap: "3px",
                        transition: "color 0.12s",
                      }}
                      onMouseEnter={e => e.currentTarget.style.color = theme.text}
                      onMouseLeave={e => e.currentTarget.style.color = theme.textMuted}
                    >
                      visit saved post
                      <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                        <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
                      </svg>
                    </button>
                  </div>
                );
              })
            )}
          </div>

          {/* Right: map */}
          <div style={{
            flex: 1,
            borderRadius: "14px",
            overflow: "hidden",
            border: `1px solid ${theme.border}`,
            position: "relative",
            background: theme.surfaceAlt,
          }}>
            {!leafletReady && (
              <div style={{
                position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center",
                background: theme.surfaceAlt, zIndex: 10,
              }}>
                <div style={{ textAlign: "center" }}>
                  <div style={{
                    width: "32px", height: "32px", borderRadius: "50%",
                    border: `2px solid ${theme.border}`,
                    borderTopColor: theme.text,
                    animation: "spin 0.7s linear infinite",
                    margin: "0 auto 10px",
                  }} />
                  <p style={{ fontFamily: "inherit", fontSize: "12px", color: theme.textMuted, margin: 0 }}>Loading map…</p>
                </div>
              </div>
            )}
            <div ref={mapRef} style={{ width: "100%", height: "100%" }} />
          </div>
        </div>
      </main>
    </div>
  );
}
