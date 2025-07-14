import Image from "next/image";
import Link from "next/link";

const mockClasses = [
  {
    id: "math101",
    name: "Algebra Fundamentals",
    teacher: "Mr. Yuen",
    term: "Fall 2025",
    color: "bg-red-500",
    img: "/class-icons/math101.png",
  },
  {
    id: "math201",
    name: "AP Calculus AB",
    teacher: "Mr. Yuen",
    term: "Fall 2025",
    color: "bg-blue-500",
    img: "/class-icons/math201.png",
  },
  {
    id: "math202",
    name: "AP Calculus BC",
    teacher: "Mr. Yuen",
    term: "Fall 2025",
    color: "bg-green-500",
    img: "/class-icons/math202.png",
  },
];

export default function DashboardPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {mockClasses.map((course) => (
          <Link
            key={course.id}
            href={`/${course.id}`} // make sure the route is correct
            className="group relative rounded-lg overflow-hidden shadow hover:shadow-md transition"
          >
            {/* Course Image */}
            <div className="relative h-40 w-full">
              <Image
                src={course.img}
                alt={`${course.name} banner`}
                fill
                className="object-cover group-hover:scale-105 transition-transform duration-300"
              />
              {/* Overlay */}
              <div className="absolute inset-0 bg-black/30 flex flex-col justify-end p-4">
                <h2 className="text-white text-lg font-semibold group-hover:underline">
                  {course.name}
                </h2>
                <p className="text-white text-sm">{course.teacher}</p>
              </div>
            </div>

            {/* Footer */}
            <div className="bg-white px-4 py-2 text-xs text-gray-500 flex justify-between items-center">
              <span>{course.term}</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
