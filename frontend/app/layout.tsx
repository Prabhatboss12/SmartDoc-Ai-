import './globals.css';
import { Toaster } from 'react-hot-toast';

export const metadata = {
  title: 'Document Q&A',
  description: 'Ask questions about your documents',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen flex flex-col">
          <main className="flex-grow">
            {children}
          </main>
          <footer className="py-4 text-center text-gray-600 dark:text-gray-400">
            Built with ❤️ by Prabhat Upadhyay | © 2024
          </footer>
        </div>
        <Toaster position="bottom-right" />
      </body>
    </html>
  );
} 