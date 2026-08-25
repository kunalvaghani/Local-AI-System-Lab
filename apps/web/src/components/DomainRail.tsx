import { routeGroups, routes } from "../navigation/routes";

type DomainRailProps = {
  activePath: string;
  onNavigate: (event: React.MouseEvent<HTMLAnchorElement>, path: string) => void;
};

function DomainRail({ activePath, onNavigate }: DomainRailProps) {
  return (
    <nav className="domain-rail" aria-label="Application areas">
      {routeGroups.map((group) => (
        <section className="nav-group" aria-labelledby={`group-${group}`} key={group}>
          <h2 id={`group-${group}`}>{group}</h2>
          {routes.filter((route) => route.group === group).map((route) => (
            <a
              aria-current={route.path === activePath ? "page" : undefined}
              href={route.path}
              key={route.path}
              onClick={(event) => onNavigate(event, route.path)}
            >
              <span aria-hidden="true">{route.shortLabel}</span>
              {route.label}
            </a>
          ))}
        </section>
      ))}
    </nav>
  );
}

export { DomainRail };
