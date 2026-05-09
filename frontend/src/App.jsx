import React, { useState, useEffect } from "react";
import Discover from "./discover";
import InsideFolder from "./insideFolder";
import PostDetail from "./postDetail";

export const LIGHT = {
  bg: "#F5F5F3",
  surface: "#FFFFFF",
  surfaceAlt: "#F5F5F3",
  border: "#E8E8E6",
  text: "#111111",
  textMuted: "#9CA3AF",
  textSub: "#6B7280",
  textMed: "#374151",
  navBg: "rgba(255,255,255,0.92)",
  cardBg: "#F0EFED",
  hover: "#EEEEED",
  inputBg: "#F5F5F3",
  modalOverlay: "rgba(0,0,0,0.35)",
};

export const DARK = {
  bg: "#111111",
  surface: "#1C1C1E",
  surfaceAlt: "#242426",
  border: "#2E2E30",
  text: "#F5F5F3",
  textMuted: "#6B7280",
  textSub: "#9CA3AF",
  textMed: "#D1D5DB",
  navBg: "rgba(28,28,30,0.92)",
  cardBg: "#1A1A1C",
  hover: "#2A2A2C",
  inputBg: "#242426",
  modalOverlay: "rgba(0,0,0,0.6)",
};

export default function App() {
  const [view, setView] = useState("discover");
  const [currentFolderName, setCurrentFolderName] = useState("");
  const [currentPostId, setCurrentPostId] = useState(null);
  const [darkMode, setDarkMode] = useState(() => localStorage.getItem("savable_dark") === "true");
  const theme = darkMode ? DARK : LIGHT;

  const [folders, setFolders] = useState(() => {
    const saved = localStorage.getItem("savable_folders");
    return saved ? JSON.parse(saved) : [
      { id: 1, name: "Favourites", color: "#4F46E5", image: "https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?w=600&auto=format&fit=crop", protected: true },
      { id: 2, name: "Food", color: "#F59E0B", image: "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=600&auto=format&fit=crop" },
      { id: 3, name: "Nature", color: "#10B981", image: "https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=600&auto=format&fit=crop" },
      { id: 4, name: "Shopping", color: "#EC4899", image: "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=600&auto=format&fit=crop" },
      { id: 5, name: "Music", color: "#8B5CF6", image: "https://images.unsplash.com/photo-1501386761578-eac5c94b800a?w=600&auto=format&fit=crop" },
      { id: 6, name: "Attractions", color: "#EF4444", image: "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=600&auto=format&fit=crop" }
    ];
  });

  const [posts, setPosts] = useState(() => {
    const saved = localStorage.getItem("savable_posts");
    return saved ? JSON.parse(saved) : [];
  });

  useEffect(() => {
    localStorage.setItem("savable_folders", JSON.stringify(folders));
    localStorage.setItem("savable_posts", JSON.stringify(posts));
  }, [folders, posts]);

  useEffect(() => {
    localStorage.setItem("savable_dark", String(darkMode));
  }, [darkMode]);

  const createNewPost = (urlData) => {
    const newId = Date.now();
    setPosts(prev => [...prev, {
      id: newId, title: "", address: "",
      categories: currentFolderName ? [currentFolderName] : [],
      rating: 0, notes: "", photos: [], externalUrls: urlData
    }]);
    setCurrentPostId(newId);
    setView("detail");
  };

  const handleUpdatePost = (updatedPost) =>
    setPosts(prev => prev.map(p => p.id === updatedPost.id ? updatedPost : p));

  const handleUpdateFolder = (oldName, newName, newColor) => {
    setFolders(prev => prev.map(f =>
      f.name === oldName ? { ...f, name: newName, color: newColor } : f
    ));
    if (oldName !== newName) {
      setPosts(prev => prev.map(p => ({
        ...p,
        categories: p.categories.map(c => c === oldName ? newName : c)
      })));
      setCurrentFolderName(newName);
    }
  };

  const handleAddFolder = (folderData) => {
    setFolders(prev => [...prev, { ...folderData, id: Date.now() }]);
  };

  const handleDeleteFolders = (folderNames) => {
    const filtered = folderNames.filter(name => name !== "Favourites");
    setFolders(prev => prev.filter(f => !filtered.includes(f.name)));
    setPosts(prev => prev.map(p => ({
      ...p,
      categories: p.categories.filter(c => !filtered.includes(c))
    })));
  };

  const handleDeleteFolder = (folderName) => {
    if (folderName === "Favourites") return;
    handleDeleteFolders([folderName]);
  };

  const handleMovePosts = (postIds, targetFolderNames) => {
    setPosts(prev => prev.map(p => {
      if (!postIds.includes(p.id)) return p;
      const newCats = p.categories.filter(c => c !== currentFolderName);
      targetFolderNames.forEach(name => { if (!newCats.includes(name)) newCats.push(name); });
      return { ...p, categories: newCats };
    }));
  };

  const handleCopyPosts = (postIds, targetFolderNames) => {
    const newPosts = [];
    setPosts(prev => {
      const updated = prev.map(p => {
        if (!postIds.includes(p.id)) return p;
        targetFolderNames.forEach(name => {
          newPosts.push({ ...p, id: Date.now() + Math.random(), categories: [name] });
        });
        return p;
      });
      return [...updated, ...newPosts];
    });
  };

  const handleRemovePosts = (postIds) => {
    setPosts(prev => prev.map(p => {
      if (!postIds.includes(p.id)) return p;
      return { ...p, categories: p.categories.filter(c => c !== currentFolderName) };
    }));
  };

  const navigateToDiscover = () => { setView("discover"); setCurrentFolderName(""); };
  const handlePostClick = (id) => { setCurrentPostId(id); setView("detail"); };
  const currentFolder = folders.find(f => f.name === currentFolderName);

  const navLinks = ["Explore", "Discover"];

  return (
    <div style={{ minHeight: "100vh", background: theme.bg, fontFamily: "'DM Sans', -apple-system, sans-serif", transition: "background 0.25s" }}>
      <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet" />

      {/* NAV */}
      <nav style={{
        position: "fixed", top: 0, left: 0, right: 0, zIndex: 100,
        background: theme.navBg,
        backdropFilter: "blur(12px)",
        WebkitBackdropFilter: "blur(12px)",
        borderBottom: `1px solid ${theme.border}`,
        height: "54px",
        display: "flex", alignItems: "center",
        padding: "0 24px",
        transition: "background 0.25s, border-color 0.25s",
      }}>
        {/* Logo */}
        <div onClick={navigateToDiscover} style={{ cursor: "pointer", display: "flex", alignItems: "center", gap: "8px", marginRight: "28px" }}>
          <div style={{ width: "30px", height: "30px", background: darkMode ? "#F5F5F3" : "#111", borderRadius: "8px", display: "flex", alignItems: "center", justifyContent: "center", transition: "background 0.25s" }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={darkMode ? "#111" : "white"} strokeWidth="2.5">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
              <circle cx="12" cy="10" r="3"/>
            </svg>
          </div>
          <span style={{ fontSize: "14px", fontWeight: "800", color: theme.text, letterSpacing: "-0.4px", transition: "color 0.25s" }}>savable</span>
        </div>

        {/* Nav links */}
        <div style={{ display: "flex", gap: "2px", flex: 1 }}>
          {navLinks.map(label => (
            <button
              key={label}
              onClick={label === "Discover" ? navigateToDiscover : undefined}
              style={{ background: "none", border: "none", cursor: "pointer", padding: "5px 12px", borderRadius: "7px", color: theme.textMuted, fontSize: "13px", fontWeight: "600", fontFamily: "inherit", transition: "all 0.12s" }}
              onMouseEnter={e => { e.currentTarget.style.background = theme.hover; e.currentTarget.style.color = theme.text; }}
              onMouseLeave={e => { e.currentTarget.style.background = "none"; e.currentTarget.style.color = theme.textMuted; }}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Dark mode toggle — replaces Settings */}
        <button
          onClick={() => setDarkMode(d => !d)}
          style={{
            display: "flex", alignItems: "center", gap: "6px",
            background: theme.surfaceAlt,
            color: theme.textMed,
            border: `1px solid ${theme.border}`,
            padding: "7px 14px", borderRadius: "20px",
            fontSize: "12px", fontWeight: "700",
            cursor: "pointer", fontFamily: "inherit",
            marginRight: "8px",
            transition: "all 0.25s",
          }}
        >
          {darkMode ? (
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <circle cx="12" cy="12" r="5"/>
              <line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/>
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
              <line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
            </svg>
          ) : (
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
            </svg>
          )}
          {darkMode ? "Light mode" : "Dark mode"}
        </button>

        <button style={{ background: darkMode ? "#F5F5F3" : "#111", color: darkMode ? "#111" : "white", border: "none", padding: "7px 16px", borderRadius: "20px", fontSize: "12px", fontWeight: "700", cursor: "pointer", fontFamily: "inherit", letterSpacing: "0.1px", transition: "all 0.25s" }}>
          Contact
        </button>
      </nav>

      <div style={{ paddingTop: "54px" }}>
        {view === "discover" && (
          <Discover
            folders={folders}
            onFolderClick={(name) => { setCurrentFolderName(name); setView("inside"); }}
            onAddFolder={handleAddFolder}
            allPosts={posts}
            onDeleteFolders={handleDeleteFolders}
            theme={theme}
          />
        )}
        {view === "inside" && (
          <InsideFolder
            folderName={currentFolderName}
            folderColor={currentFolder?.color}
            onBack={navigateToDiscover}
            onPostClick={handlePostClick}
            onAddPost={createNewPost}
            posts={posts.filter(p => p.categories.includes(currentFolderName))}
            allFolders={folders}
            allPosts={posts}
            onUpdateFolder={handleUpdateFolder}
            onMovePosts={handleMovePosts}
            onCopyPosts={handleCopyPosts}
            onRemovePosts={handleRemovePosts}
            onAddFolder={handleAddFolder}
            onDeleteFolder={handleDeleteFolder}
            theme={theme}
          />
        )}
        {view === "detail" && (
          <PostDetail
            onBack={() => setView("inside")}
            data={posts.find(p => p.id === currentPostId) || {}}
            setData={handleUpdatePost}
            allFolders={folders}
            theme={theme}
          />
        )}
      </div>
    </div>
  );
}
