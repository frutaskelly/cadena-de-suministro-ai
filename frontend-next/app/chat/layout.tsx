// Layout especifico del chat — quita el max-width y padding del main
// para que ocupe toda la pantalla disponible.
export default function ChatLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <div className="h-screen overflow-hidden">{children}</div>;
}
