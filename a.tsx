<main>  ← No flexbox on main
  {/* Fixed Header Section */}
  <div className="w-full">  ← Dedicated header container
    <h1>Deep Research Health Agent 3.0</h1>
  </div>

  {/* Content Section */}
  <div style={{ height: "calc(100vh - 120px)" }}>  ← Calculated height
    <LoginForm /> or <PatientForm />
  </div>
</main>
