"use client";

import type React from "react";
import { useState, useRef, useEffect } from "react";
import { PatientForm, type PatientFormValues } from "./PatientForm";
import { ProgressView } from "./ProgressView";
import { ResultsView, type AnalysisResult } from "./ResultsView";
import { LoginForm } from "./LoginForm";
import AgentService from "./AgentService";

type Stage = "form" | "processing" | "complete";

export const App: React.FC = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [stage, setStage] = useState<Stage>("form");
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [patient, setPatient] = useState<PatientFormValues>({
    firstName: "",
    lastName: "",
    dob: "",
    gender: "",
    zip: "",
    ssn: "",
  });
  const [isProcessing, setIsProcessing] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const sectionRef = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    if (stage === "processing" && sectionRef.current) {
      sectionRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [stage]);

  async function handleSubmit(values: PatientFormValues) {
    setPatient(values);
    setStage("processing");
    setIsProcessing(true);

    try {
      const payload: {
        first_name: string;
        last_name: string;
        ssn: string;
        date_of_birth: string;
        gender: "M" | "F";
        zip_code: string;
      } = {
        first_name: values.firstName.trim(),
        last_name: values.lastName.trim(),
        ssn: values.ssn.trim(),
        date_of_birth: values.dob,
        gender: values.gender === "Female" ? "F" : "M",
        zip_code: values.zip.trim(),
      };


      const apiResponse = await AgentService.runAnalysisSync(payload);

      if (!apiResponse.success || !apiResponse.data?.analysis_results) {
        throw new Error("Invalid response from analysis API");
      }

      const analysis = apiResponse.data.analysis_results;

      const transformedResult: AnalysisResult = {

        claimsData: analysis.deidentified_data.medical || [],
        claimsAnalysis: analysis.deidentified_data?.pharmacy || [],
        mcidClaims: [analysis.deidentified_data.mcid || {}],

        extractionSummary: {
          serviceCodeCount:
            analysis.api_outputs?.medical?.body?.MEDICAL_CLAIMS
              ?.flatMap((claim: any) =>
                claim.claim_lines?.map((line: any) => line.hlth_srvc_cd).filter((code: string) => !!code)
              ).length || 0,

          ICD10CodeCount: Object.keys(
            analysis.structured_extractions?.medical?.code_meanings?.diagnosis_code_meanings || {}
          ).length,

          medicalRecordCount: analysis.structured_extractions?.medical?.extraction_summary?.total_hlth_srvc_records || 0,

          billingProviderCount:
            Array.from(
              new Set(
                analysis.api_outputs?.medical?.body?.MEDICAL_CLAIMS
                  ?.map((claim: any) => claim.billg_prov_nm)
                  .filter((name: string) => !!name)
              )
            ).length || analysis.structured_extractions?.medical?.extraction_summary?.total_diagnosis_codes || 0,
        },

        pharmacySummary: {
          ndcCodeCount: Object.keys(
            analysis.structured_extractions?.pharmacy?.code_meanings?.ndc_code_meanings || {}
          ).length,

          medicationCount: Object.keys(
            analysis.structured_extractions?.pharmacy?.code_meanings?.medication_meanings || {}
          ).length,

          pharmacyRecordCount:
            analysis.api_outputs?.pharmacy?.body?.PHARMACY_CLAIMS?.length || 0,
          prescribingProviderCount: Array.from(
            new Set(
              analysis.api_outputs?.pharmacy?.body?.PHARMACY_CLAIMS
                ?.map((claim: any) => claim.prscrbg_prov_nm)
                .filter((name: string) => !!name)
            )
          ).length || 0,
        },

        icd10Data: analysis.api_outputs?.medical?.body?.MEDICAL_CLAIMS
          ?.filter((claim: any) => claim.diag_1_50_cd)
          .flatMap((claim: any, index: number) => {
            const diagnosisCodes = claim.diag_1_50_cd.split(",");
            return diagnosisCodes.map((code: string, position: number) => ({
              code: code,
              meaning: analysis.structured_extractions?.medical?.code_meanings?.diagnosis_code_meanings?.[code] || "",
              date: claim.clm_rcvd_dt || "",
              provider: claim.billg_prov_nm || "",
              zip: claim.billg_prov_zip_cd || "",
              // position: position + 1,
              // source: "diag_1_50_cd",
              // path: `MEDICAL_CLAIMS[${index}]`
            }));
          }) || [],

        serviceCodeData: analysis.api_outputs?.medical?.body?.MEDICAL_CLAIMS
          ?.flatMap((claim: any, claimIndex: number) =>
            claim.claim_lines?.map((line: any) => ({
              serviceCode: line.hlth_srvc_cd || "",
              serviceDescription: analysis.structured_extractions?.medical?.code_meanings?.service_code_meanings?.[line.hlth_srvc_cd] || "",
              date: line.clm_line_srvc_end_dt || "",
              path: `MEDICAL_CLAIMS[${claimIndex}].claim_lines[${line.clm_line_nbr || 0}]`
            }))
          ) || [],

        ndcData: analysis.api_outputs?.pharmacy?.body?.PHARMACY_CLAIMS
          ?.map((claim: any, index: number) => ({
            code: claim.ndc || "",
            medication: claim.lbl_nm || "",
            date: claim.rx_filled_dt || "",
            description: analysis.structured_extractions?.pharmacy?.code_meanings?.ndc_code_meanings?.[claim.ndc] || "",
            path: `PHARMACY_CLAIMS[${index}]`
          })) || [],

        medicationData: analysis.api_outputs?.pharmacy?.body?.PHARMACY_CLAIMS
          ?.map((claim: any, index: number) => ({
            ndcCode: claim.ndc || "",
            medication: claim.lbl_nm || "",
            fillDate: claim.rx_filled_dt || "",
            description: analysis.structured_extractions?.pharmacy?.code_meanings?.medication_meanings?.[claim.lbl_nm] || "",
            billingProvider: claim.billg_prov_nm || "",
            prescribingProvider: claim.prscrbg_prov_nm || "",
            path: `PHARMACY_CLAIMS[${index}]`
          })) || [],

        entities: [
          { type: "Diabetes Status", value: analysis.entity_extraction?.diabetics || "Unknown" },
          { type: "Age", value: String(analysis.entity_extraction?.age || "unknown") },
          { type: "Age Group", value: analysis.entity_extraction?.age_group || "Unknown" },
          { type: "Smoking Status", value: analysis.entity_extraction?.smoking || "Unknown" },
          { type: "Alcohol Use", value: analysis.entity_extraction?.alcohol || "Unknown" },
          { type: "Blood Pressure", value: analysis.entity_extraction?.blood_pressure || "Unknown" },
        ],
        healthTrajectory: analysis.health_trajectory,
        heartRisk: {
          score: Math.round((analysis.heart_attack_prediction?.raw_risk_score || 0) * 100),
          level: analysis.heart_attack_prediction?.risk_category || "Unknown",
        },
      };

      setResult(transformedResult);
      setIsProcessing(false);
      setStage("complete");
    } catch (e) {
      console.error("Analysis failed:", e);
      setIsProcessing(false);
      setStage("form");
    }
  }

  function handleComplete() {
    setStage("complete");
    setShowResults(true);
  }

  function handleRunAgain() {
    setStage("form");
    setResult(null);
    setIsProcessing(false);
    setShowResults(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function handleLoginSuccess() {
    setIsLoggedIn(true);
  }

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
          {/* Fixed Header Section */}
          <div className="w-full" style={{ flexShrink: 0 }}>
            <h1
              className="text-4xl font-extrabold text-center pt-8 pb-4 bg-gradient-to-r from-blue-900 via-indigo-500 to-sky-300 bg-clip-text text-transparent"
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
          </div>

          {/* Content Section */}
          <div 
            className="flex justify-end items-center pr-4 pl-10"
            style={{
              height: "calc(100vh - 120px)",
            }}
          >
            <LoginForm onLoginSuccess={handleLoginSuccess} />
          </div>
        </main>
      </div>
    );
  }

  // Show main application after login
  return (
    <div className="w-full">
      <main
        className={`relative w-full bg-cover bg-no-repeat bg-center transition-all duration-700`}
        style={{
          backgroundImage: "url('/bg-image.png')",
          height: stage === "form" ? "100vh" : "78vh",
        }}
      >
        {/* Fixed Header Section */}
        <div className="w-full" style={{ flexShrink: 0 }}>
          <h1
            className="text-4xl font-extrabold text-center pt-8 pb-4 bg-gradient-to-r from-blue-900 via-indigo-500 to-sky-300 bg-clip-text text-transparent"
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
        </div>

        {/* Content Section */}
        <div 
          className="flex justify-end items-center px-10"
          style={{
            height: stage === "form" ? "calc(100vh - 120px)" : "calc(78vh - 120px)",
          }}
        >
          <PatientForm onSubmit={handleSubmit} initialValues={patient} />
        </div>
      </main>

      <section className="px-6 py-8" style={{ background: "#fff" }}>
        {stage === "processing" && <ProgressView isProcessing={isProcessing} onComplete={handleComplete} />}
        {stage === "complete" && result && <ResultsView result={result} onRunAgain={handleRunAgain} />}
      </section>
    </div>
  );
};
