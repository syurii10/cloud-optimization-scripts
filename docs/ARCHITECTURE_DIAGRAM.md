# 📐 Діаграма архітектури системи

## Візуалізація в Mermaid (для GitHub/Markdown)

```mermaid
graph TB
    subgraph User["👤 КОРИСТУВАЧ"]
        DevOps["DevOps Engineer"]
    end

    subgraph Control["🎛️ CONTROL LAYER"]
        CP["Control Panel<br/>(Interactive Config)"]
        DB["Live Dashboard<br/>(HTTP:8080)"]
    end

    subgraph Engine["⚙️ CORE OPTIMIZATION ENGINE"]
        subgraph DataCollection["1️⃣ DATA COLLECTION"]
            RS["Request Simulator<br/>(Load Generator)"]
            MC["Metrics Collector<br/>(CPU/RAM/Latency)"]
        end

        subgraph MCDM["2️⃣ MCDM ANALYSIS"]
            OPT["TOPSIS Optimizer<br/>5 Criteria<br/>Performance 35%<br/>Response 25%<br/>CPU 15%<br/>Memory 15%<br/>Cost 10%"]
            SA["Sensitivity Analyzer<br/>(Weight Variations)"]
            COMP["Method Comparator<br/>(TOPSIS/SAW/WPM)"]
        end

        subgraph Reporting["3️⃣ REPORTING"]
            VIS["Visualizer<br/>(6 Charts)"]
            REP["Report Generator<br/>(Markdown)"]
            COST["Cost Predictor<br/>(AWS Pricing)"]
        end
    end

    subgraph Storage["💾 RESULTS STORAGE"]
        JSON["JSON Files<br/>(results/data/)"]
        CHARTS["Charts<br/>(results/charts/)"]
    end

    subgraph AWS["☁️ AWS INFRASTRUCTURE (Terraform)"]
        subgraph Instances["EC2 Instances"]
            MICRO["t3.micro<br/>1 vCPU, 1GB<br/>$0.0104/hr"]
            SMALL["t3.small<br/>2 vCPU, 2GB<br/>$0.0208/hr"]
            MEDIUM["t3.medium<br/>2 vCPU, 4GB<br/>$0.0416/hr"]
        end
        SERVER["CPU-Intensive Server<br/>(Flask :80)"]
    end

    subgraph VCS["📦 VERSION CONTROL"]
        GH["GitHub Repository"]
    end

    DevOps -->|"1. Configure Test"| CP
    CP -->|"2. Deploy"| MICRO
    CP -->|"2. Deploy"| SMALL
    CP -->|"2. Deploy"| MEDIUM

    MICRO --> SERVER
    SMALL --> SERVER
    MEDIUM --> SERVER

    RS -->|"3. Load Test<br/>(500/2000/5000 RPS)"| SERVER
    SERVER -->|"4. Metrics"| MC

    MC -->|"5. Raw Data"| OPT
    OPT -->|"6. TOPSIS Scores"| SA
    SA -->|"7. Stability Data"| COMP

    COMP -->|"8. Validated Results"| VIS
    COMP -->|"9. Analysis Data"| COST

    VIS -->|"10. Save Charts"| CHARTS
    COST -->|"11. Save JSON"| JSON

    CHARTS -->|"12. Generate"| REP
    JSON -->|"12. Generate"| REP

    CHARTS -->|"13. Display"| DB
    JSON -->|"13. Display"| DB

    DB -->|"14. View Results"| DevOps

    CP --> GH
    OPT --> GH
    SA --> GH
    COMP --> GH
    VIS --> GH
    REP --> GH

    style DevOps fill:#667eea,color:#fff
    style CP fill:#4ECDC4,color:#000
    style DB fill:#4ECDC4,color:#000
    style OPT fill:#95E1D3,color:#000
    style SA fill:#95E1D3,color:#000
    style COMP fill:#95E1D3,color:#000
    style VIS fill:#FFD93D,color:#000
    style REP fill:#FFD93D,color:#000
    style COST fill:#FFD93D,color:#000
    style MICRO fill:#FF6B6B,color:#fff
    style SMALL fill:#4ECDC4,color:#000
    style MEDIUM fill:#95E1D3,color:#000
```

---

## Діаграма послідовності (Sequence Diagram)

```mermaid
sequenceDiagram
    actor User as DevOps Engineer
    participant CP as Control Panel
    participant TF as Terraform
    participant EC2 as EC2 Instances
    participant SRV as CPU Server
    participant RS as Request Simulator
    participant OPT as TOPSIS Optimizer
    participant SA as Sensitivity Analysis
    participant CMP as Method Comparison
    participant VIS as Visualizer
    participant DB as Dashboard

    User->>CP: 1. Configure test parameters
    CP->>User: Show configuration UI
    User->>CP: Confirm (RPS: 500/2000/5000)

    CP->>TF: 2. terraform apply
    TF->>EC2: Deploy 3 instances
    EC2->>SRV: Start Flask server (:80)
    SRV-->>EC2: Health check OK
    EC2-->>TF: Deployment complete
    TF-->>CP: Infrastructure ready

    loop For each instance & RPS level
        CP->>RS: 3. Start load test
        RS->>SRV: Send HTTP requests (60s)
        SRV-->>RS: Response + metrics
        RS->>RS: Collect CPU, RAM, latency
        RS-->>CP: Save test_results.json
    end

    CP->>OPT: 4. Run optimization
    OPT->>OPT: Build decision matrix
    OPT->>OPT: Normalize & weight
    OPT->>OPT: Calculate TOPSIS scores
    OPT-->>CP: optimization_results.json

    CP->>SA: 5. Sensitivity analysis
    SA->>SA: Vary weights 5% to 70%
    SA->>SA: Detect breakpoints
    SA->>SA: Calculate stability indices
    SA-->>CP: sensitivity_analysis.json

    CP->>CMP: 6. Method comparison
    CMP->>CMP: Run TOPSIS, SAW, WPM
    CMP->>CMP: Calculate Kendall Tau
    CMP-->>CP: method_comparison.json

    CP->>VIS: 7. Generate visualizations
    VIS->>VIS: Create 6 charts (300 DPI)
    VIS-->>CP: Save to results/charts/

    User->>DB: 8. Open http://localhost:8080
    DB->>DB: Load JSON + charts
    DB-->>User: Display live dashboard

    CP->>TF: 9. terraform destroy
    TF->>EC2: Terminate instances
    EC2-->>TF: Cleanup complete
```

---

## Діаграма компонентів (Component Diagram)

```mermaid
graph LR
    subgraph Scripts["📂 scripts/"]
        OPT[optimizer.py]
        SA[sensitivity_analysis.py]
        MC[method_comparison.py]
        CP[cost_predictor.py]
        RG[report_generator.py]
        VIS[visualize_results.py]
        RS[request_simulator.py]
        LD[live_dashboard.py]
        CONT[control_panel.py]
    end

    subgraph Results["📂 results/"]
        DATA[data/<br/>32 JSON files]
        CHARTS[charts/<br/>6 PNG files]
        REP[reports/<br/>Markdown]
    end

    subgraph IaC["📂 terraform/"]
        EC2[ec2.tf]
        VPC[vpc.tf]
        VAR[variables.tf]
    end

    subgraph Docs["📂 docs/"]
        ARCH[ARCHITECTURE.md]
        COMP_[comparison_analysis.md]
        WOW[WOW_IMPROVEMENTS.md]
    end

    RS --> DATA
    OPT --> DATA
    SA --> DATA
    MC --> DATA
    CP --> DATA

    VIS --> DATA
    VIS --> CHARTS

    RG --> DATA
    RG --> CHARTS
    RG --> REP

    LD --> DATA
    LD --> CHARTS

    CONT --> EC2

    style OPT fill:#95E1D3
    style SA fill:#95E1D3
    style MC fill:#95E1D3
    style VIS fill:#FFD93D
    style LD fill:#4ECDC4
```

---

## Діаграма розгортання (Deployment Diagram)

```mermaid
graph TB
    subgraph Local["💻 LOCAL MACHINE"]
        Python["Python 3.12+<br/>numpy, scipy, matplotlib"]
        Scripts["Optimization Scripts"]
        Terraform["Terraform CLI"]
    end

    subgraph Cloud["☁️ AWS CLOUD (us-east-1)"]
        subgraph VPC["VPC (10.0.0.0/16)"]
            subgraph Subnet["Public Subnet"]
                T3M["t3.micro<br/>Instance 1<br/>10.0.1.10"]
                T3S["t3.small<br/>Instance 2<br/>10.0.1.11"]
                T3MD["t3.medium<br/>Instance 3<br/>10.0.1.12"]
            end

            SG["Security Group<br/>(Port 80, 22)"]
        end

        IGW["Internet Gateway"]
    end

    subgraph Browser["🌐 BROWSER"]
        Dashboard["Live Dashboard<br/>http://localhost:8080"]
    end

    Terraform -->|"terraform apply"| VPC
    Scripts -->|"HTTP requests"| T3M
    Scripts -->|"HTTP requests"| T3S
    Scripts -->|"HTTP requests"| T3MD

    T3M -.->|"Response + Metrics"| Scripts
    T3S -.->|"Response + Metrics"| Scripts
    T3MD -.->|"Response + Metrics"| Scripts

    Subnet --> SG
    SG --> IGW

    Python -->|"Start HTTP server"| Dashboard
    Dashboard -->|"Display results"| Browser

    style T3M fill:#FF6B6B,color:#fff
    style T3S fill:#4ECDC4
    style T3MD fill:#95E1D3
    style Dashboard fill:#667eea,color:#fff
```

---

## Потік даних (Data Flow Diagram)

```mermaid
flowchart TD
    Start([START]) --> Config[Configure Test Parameters]
    Config --> Deploy{Deploy<br/>Infrastructure?}

    Deploy -->|Yes| TF[Terraform Apply]
    Deploy -->|No| LoadData[Load Existing Data]

    TF --> Wait[Wait 5-7 min for init]
    Wait --> Tests[Run Load Tests]

    Tests --> T1[Test t3.micro @ 500 RPS]
    Tests --> T2[Test t3.micro @ 2000 RPS]
    Tests --> T3[Test t3.micro @ 5000 RPS]
    Tests --> T4[Test t3.small @ 500 RPS]
    Tests --> T5[Test t3.small @ 2000 RPS]
    Tests --> T6[Test t3.small @ 5000 RPS]
    Tests --> T7[Test t3.medium @ 500 RPS]
    Tests --> T8[Test t3.medium @ 2000 RPS]
    Tests --> T9[Test t3.medium @ 5000 RPS]

    T1 --> Collect[Collect All Results]
    T2 --> Collect
    T3 --> Collect
    T4 --> Collect
    T5 --> Collect
    T6 --> Collect
    T7 --> Collect
    T8 --> Collect
    T9 --> Collect

    LoadData --> Collect

    Collect --> Matrix[Build Decision Matrix]
    Matrix --> Normalize[Normalize Data]
    Normalize --> Weight[Apply Weights]
    Weight --> Ideal[Calculate Ideal Solutions]
    Ideal --> Distance[Calculate Distances]
    Distance --> Score[Calculate TOPSIS Scores]
    Score --> Rank[Rank Alternatives]

    Rank --> Sensitivity[Sensitivity Analysis]
    Sensitivity --> Vary[Vary Each Weight 5-70%]
    Vary --> Breakpoints[Detect Breakpoints]
    Breakpoints --> Stability[Calculate Stability]

    Stability --> Methods[Compare Methods]
    Methods --> TOPSIS[Run TOPSIS]
    Methods --> SAW[Run SAW]
    Methods --> WPM[Run WPM]

    TOPSIS --> Kendall[Kendall Tau Correlation]
    SAW --> Kendall
    WPM --> Kendall

    Kendall --> Consensus{Consensus?}
    Consensus -->|Yes| Validated[Results Validated]
    Consensus -->|No| Warning[Warning: Low Consensus]

    Warning --> Validated

    Validated --> Cost[Cost Prediction]
    Cost --> Charts[Generate 6 Charts]
    Charts --> Report[Generate Report]

    Report --> Dashboard[Launch Dashboard]
    Dashboard --> View[View in Browser]

    View --> Destroy{Destroy<br/>Infrastructure?}
    Destroy -->|Yes| Cleanup[Terraform Destroy]
    Destroy -->|No| Keep[Keep Running]

    Cleanup --> End([END])
    Keep --> End

    style Start fill:#95E1D3
    style Config fill:#4ECDC4
    style Score fill:#FFD93D
    style Validated fill:#95E1D3
    style Dashboard fill:#667eea,color:#fff
    style End fill:#95E1D3
```

---

## Алгоритм TOPSIS (Покроковий)

```mermaid
flowchart TD
    Input[INPUT:<br/>Decision Matrix X<br/>m alternatives × n criteria<br/>Weights W<br/>Benefit/Cost indicators]

    Input --> Step1[STEP 1: Normalization<br/>r_ij = x_ij / sqrt(sum x_ij²)]

    Step1 --> Step2[STEP 2: Weighted Matrix<br/>v_ij = w_j × r_ij]

    Step2 --> Step3A[STEP 3a: Ideal Solution A+<br/>max(v_ij) for benefit<br/>min(v_ij) for cost]
    Step2 --> Step3B[STEP 3b: Anti-Ideal Solution A-<br/>min(v_ij) for benefit<br/>max(v_ij) for cost]

    Step3A --> Step4[STEP 4: Calculate Distances]
    Step3B --> Step4

    Step4 --> D_plus[D+ = sqrt(sum (v_ij - A+_j)²)]
    Step4 --> D_minus[D- = sqrt(sum (v_ij - A-_j)²)]

    D_plus --> Step5[STEP 5: TOPSIS Score<br/>C_i = D- / (D+ + D-)]
    D_minus --> Step5

    Step5 --> Step6[STEP 6: Rank Alternatives<br/>Sort by C_i descending]

    Step6 --> Output[OUTPUT:<br/>Rankings<br/>Scores (0-1)<br/>Best Alternative]

    style Input fill:#4ECDC4
    style Step1 fill:#95E1D3
    style Step2 fill:#95E1D3
    style Step3A fill:#FFD93D
    style Step3B fill:#FFD93D
    style Step5 fill:#FF6B6B,color:#fff
    style Output fill:#95E1D3
```

---

## Приклад використання (Use Case)

```mermaid
graph TB
    Actor[DevOps Engineer<br/>Ukrainian Armed Forces]

    subgraph UseCases["USE CASES"]
        UC1[Optimize Delta System<br/>Artillery Calculations<br/>Requirement: <100ms latency]
        UC2[Optimize Aeneas System<br/>Intelligence Processing<br/>Requirement: 500GB/day]
        UC3[Optimize Cyber Defense<br/>DDoS Resilience<br/>Requirement: 5000 RPS]
        UC4[Optimize Logistix<br/>Supply Chain<br/>Requirement: Cost-effective]
    end

    subgraph System["TOPSIS OPTIMIZATION SYSTEM"]
        Config[Configure Criteria Weights]
        Test[Run Load Tests]
        Optimize[TOPSIS Analysis]
        Results[View Results]
    end

    Actor --> UC1
    Actor --> UC2
    Actor --> UC3
    Actor --> UC4

    UC1 --> Config
    UC2 --> Config
    UC3 --> Config
    UC4 --> Config

    Config --> Test
    Test --> Optimize
    Optimize --> Results

    Results -->|"t3.medium<br/>52ms latency"| Decision1[Deploy to Production]
    Results -->|"t3.medium<br/>Highest throughput"| Decision2[Deploy to Production]
    Results -->|"t3.medium<br/>Stable under load"| Decision3[Deploy to Production]
    Results -->|"t3.small<br/>Best cost/performance"| Decision4[Deploy to Production]

    Decision1 --> Impact1[Saves Lives<br/>Real-time targeting]
    Decision2 --> Impact2[Faster Intel<br/>Better decisions]
    Decision3 --> Impact3[System Uptime<br/>During attacks]
    Decision4 --> Impact4[$4.5M/year savings<br/>15 Bayraktar TB2 drones]

    style Actor fill:#667eea,color:#fff
    style UC1 fill:#FF6B6B,color:#fff
    style UC2 fill:#FF6B6B,color:#fff
    style UC3 fill:#FF6B6B,color:#fff
    style UC4 fill:#FF6B6B,color:#fff
    style Impact1 fill:#95E1D3
    style Impact2 fill:#95E1D3
    style Impact3 fill:#95E1D3
    style Impact4 fill:#95E1D3
```

---

## Як використовувати ці діаграми

### У презентації PowerPoint:
1. Відкрийте цей файл на GitHub (діаграми автоматично рендеряться)
2. Зробіть screenshot кожної діаграми
3. Вставте в слайди

### У звіті (PDF):
1. Використайте online Mermaid renderer: https://mermaid.live/
2. Скопіюйте код діаграми
3. Експортуйте як PNG/SVG
4. Вставте в документ

### У GitHub README:
```markdown
# Architecture

See [ARCHITECTURE_DIAGRAM.md](docs/ARCHITECTURE_DIAGRAM.md) for detailed system diagrams.
```

Діаграми автоматично відображатимуться на GitHub!

---

*Створено для магістерської роботи, 2025*
*Використані інструменти: Mermaid Diagrams (Markdown-native)*
