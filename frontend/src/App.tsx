import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import About from './pages/About'
import Book from './pages/Book'
import Home from './pages/Home'
import MemoryPage from './pages/MemoryPage'
import Record from './pages/Record'
import Remembrance from './pages/Remembrance'
import Review from './pages/Review'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="record" element={<Record />} />
        <Route path="recordings/:id" element={<Review />} />
        <Route path="memories/:id" element={<MemoryPage />} />
        <Route path="people/:id" element={<Remembrance />} />
        <Route path="book" element={<Book />} />
        <Route path="about" element={<About />} />
      </Route>
    </Routes>
  )
}
