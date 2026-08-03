/**

 * Demo layout — 比赛专用，无侧边栏，干净暖色背景
 */

export default function DemoLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen" style={{ background: "linear-gradient(180deg, #FFF8E7 0%, #FFFDF5 40%, #FFFFFF 100%)" }}>
      {children}
    </div>
  );
}
