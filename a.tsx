  // Show login screen if not logged in
  if (!isLoggedIn) {
    return (
      <div className="w-full">
        <main
          className="relative w-full bg-cover bg-no-repeat bg-center"
          style={{
            backgroundImage: "url('/bg-image.png')",
            height: "100vh",
          }}
        >
          <h1
            className="text-4xl font-extrabold text-center pt-8 relative bg-gradient-to-r from-blue-900 via-indigo-500 to-sky-300 bg-clip-text text-transparent"
            style={{
              fontFamily:
                'ui-sans-serif, system-ui, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji"',
            }}
          >
            <span className="shine-text">
              Deep Research Health Agent 3.0
            </span>

            <style>
              {`
      .shine-text {
        background-image: linear-gradient(
          90deg,
          transparent,
          rgba(255,255,255,0.9),
          transparent
        );
        background-repeat: no-repeat;
        background-size: 200% 100%;
        -webkit-background-clip: text;
        background-clip: text;
        animation: shine 5s ease-in-out infinite;
        display: inline-block;
      }
 
      @keyframes shine {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
      }
    `}
            </style>
          </h1>

          <LoginForm onLoginSuccess={handleLoginSuccess} />
        </main>
      </div>
    );
  }

